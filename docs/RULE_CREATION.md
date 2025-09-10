# Rule Creation Guide

This guide explains how to create and manage business rules in the EQ Prepaid Backend system. Rules are used to define complex SQL queries for calculating commercial offer revenue (Chiffre d'Affaires) and other business metrics.

## Table of Contents

- [Overview](#overview)
- [Rule Structure](#rule-structure)
- [Configuration Schema](#configuration-schema)
- [API Endpoints](#api-endpoints)
- [Examples](#examples)
- [Best Practices](#best-practices)

## Overview

The rule system allows you to:
- Define complex SQL queries through JSON configuration
- Calculate revenue (CA) for different offer types
- Filter data by profile types, balance types, and time periods
- Generate parameterized queries for flexible reporting
- Manage rule lifecycle (DRAFT, ACTIVE, INACTIVE)

## Rule Structure

A rule consists of the following components:

### Basic Properties
- **name**: Human-readable rule name
- **profile_type**: Target profile type (`PREPAID`, `HYBRID`)
- **balance_type**: Balance type to analyze (`MAIN_BALANCE`, `CRED`)
- **status**: Rule status (`DRAFT`, `ACTIVE`, `INACTIVE`)
- **section_id**: Reference to a section for organization
- **database_table_name**: List of database tables used by the rule

### Configuration Object
The `config` field contains the SQL query definition in JSON format.

## Configuration Schema

### Root Structure
```json
{
  "select": { ... },
  "from": { ... },
  "joins": [ ... ],
  "conditions": { ... },
  "group_by": [ ... ],
  "having": [ ... ],
  "order_by": [ ... ],
  "parameters": { ... }
}
```

### SELECT Clause
```json
{
  "select": {
    "fields": [
      {
        "name": "field_name",
        "expression": "SQL_EXPRESSION",
        "alias": "column_alias"
      }
    ],
    "aggregations": ["SUM", "COUNT", "AVG"]
  }
}
```

### FROM Clause
```json
{
  "from": {
    "main_table": "table_name",
    "alias": "t"
  }
}
```

### JOINS
```json
{
  "joins": [
    {
      "type": "INNER|LEFT|RIGHT",
      "table": "table_name",
      "alias": "alias",
      "on": "join_condition"
    }
  ]
}
```

### CONDITIONS (WHERE)
```json
{
  "conditions": {
    "where": [
      {
        "field": "column_name",
        "operator": "=|>|<|>=|<=|IN|BETWEEN",
        "value": "value_or_parameter",
        "logical_operator": "AND|OR|null"
      }
    ]
  }
}
```

### PARAMETERS
```json
{
  "parameters": {
    "param_name": {
      "type": "string|integer|date|enum",
      "required": true|false,
      "default": "default_value",
      "description": "Parameter description",
      "values": ["enum_value1", "enum_value2"]
    }
  }
}
```

## API Endpoints

### Create a Rule
```http
POST /api/v1/rules/
Content-Type: application/json

{
  "name": "Monthly Revenue Analysis",
  "profile_type": "PREPAID",
  "balance_type": "MAIN_BALANCE",
  "section_id": "uuid-here",
  "database_table_name": ["transactions", "offers"],
  "config": { ... }
}
```

### Get All Rules
```http
GET /api/v1/rules/?page=1&size=10&profile_type_filter=PREPAID
```

### Get Rule by ID
```http
GET /api/v1/rules/{rule_id}
```

### Generate SQL from Rule
```http
POST /api/v1/rules/{rule_id}/sql
Content-Type: application/json

{
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "profile_type": "PREPAID"
}
```

## Examples

### Example 1: Simple Revenue Calculation

```json
{
  "name": "Simple Prepaid Revenue",
  "profile_type": "PREPAID",
  "balance_type": "MAIN_BALANCE",
  "section_id": "section-uuid",
  "database_table_name": ["transactions", "offers"],
  "config": {
    "select": {
      "fields": [
        {
          "name": "total_ca",
          "expression": "SUM(amount)",
          "alias": "chiffre_affaires"
        },
        {
          "name": "offer_id",
          "expression": "offer_id",
          "alias": "offre_commerciale"
        }
      ],
      "aggregations": ["SUM", "COUNT"]
    },
    "from": {
      "main_table": "transactions",
      "alias": "t"
    },
    "joins": [
      {
        "type": "INNER",
        "table": "offers",
        "alias": "o",
        "on": "t.offer_id = o.id"
      }
    ],
    "conditions": {
      "where": [
        {
          "field": "t.transaction_type",
          "operator": "=",
          "value": "PURCHASE",
          "logical_operator": "AND"
        },
        {
          "field": "t.status",
          "operator": "=",
          "value": "COMPLETED",
          "logical_operator": "AND"
        },
        {
          "field": "o.profile_type",
          "operator": "=",
          "value": "PREPAID",
          "logical_operator": "AND"
        },
        {
          "field": "t.created_at",
          "operator": ">=",
          "value": "{{start_date}}",
          "logical_operator": "AND"
        },
        {
          "field": "t.created_at",
          "operator": "<=",
          "value": "{{end_date}}",
          "logical_operator": null
        }
      ]
    },
    "group_by": ["offer_id"],
    "having": [
      {
        "field": "SUM(amount)",
        "operator": ">",
        "value": 0
      }
    ],
    "order_by": [
      {
        "field": "chiffre_affaires",
        "direction": "DESC"
      }
    ],
    "parameters": {
      "start_date": {
        "type": "date",
        "required": true,
        "description": "Date de début pour le calcul du CA"
      },
      "end_date": {
        "type": "date",
        "required": true,
        "description": "Date de fin pour le calcul du CA"
      }
    }
  }
}
```

**Generated SQL:**
```sql
SELECT
  SUM(amount) AS chiffre_affaires,
  offer_id AS offre_commerciale
FROM transactions t
INNER JOIN offers o ON t.offer_id = o.id
WHERE
  t.transaction_type = 'PURCHASE'
  AND t.status = 'COMPLETED'
  AND o.profile_type = 'PREPAID'
  AND t.created_at >= '2024-01-01'
  AND t.created_at <= '2024-12-31'
GROUP BY offer_id
HAVING SUM(amount) > 0
ORDER BY chiffre_affaires DESC;
```

### Example 2: Complex Revenue with Balance Types

```json
{
  "name": "Complex Balance Type Analysis",
  "profile_type": "HYBRID",
  "balance_type": "MAIN_BALANCE",
  "section_id": "section-uuid",
  "database_table_name": ["transactions", "offers", "balance_operations"],
  "config": {
    "select": {
      "fields": [
        {
          "name": "ca_main_balance",
          "expression": "SUM(CASE WHEN b.balance_type = 'MAIN_BALANCE' THEN t.amount ELSE 0 END)",
          "alias": "ca_solde_principal"
        },
        {
          "name": "ca_credit",
          "expression": "SUM(CASE WHEN b.balance_type = 'CRED' THEN t.amount ELSE 0 END)",
          "alias": "ca_credit"
        },
        {
          "name": "transaction_count",
          "expression": "COUNT(*)",
          "alias": "nombre_transactions"
        },
        {
          "name": "offer_name",
          "expression": "o.name",
          "alias": "nom_offre"
        }
      ]
    },
    "from": {
      "main_table": "transactions",
      "alias": "t"
    },
    "joins": [
      {
        "type": "INNER",
        "table": "offers",
        "alias": "o",
        "on": "t.offer_id = o.id"
      },
      {
        "type": "INNER",
        "table": "balance_operations",
        "alias": "b",
        "on": "t.id = b.transaction_id"
      },
      {
        "type": "LEFT",
        "table": "customers",
        "alias": "c",
        "on": "t.customer_id = c.id"
      },
      {
        "type": "LEFT",
        "table": "customer_profiles",
        "alias": "cp",
        "on": "c.id = cp.customer_id"
      }
    ],
    "conditions": {
      "where": [
        {
          "field": "t.status",
          "operator": "IN",
          "value": ["COMPLETED", "VALIDATED"],
          "logical_operator": "AND"
        },
        {
          "field": "cp.profile_type",
          "operator": "=",
          "value": "{{profile_type}}",
          "logical_operator": "AND"
        },
        {
          "field": "b.balance_type",
          "operator": "IN",
          "value": ["MAIN_BALANCE", "CRED"],
          "logical_operator": "AND"
        },
        {
          "field": "t.amount",
          "operator": ">",
          "value": 0,
          "logical_operator": "AND"
        },
        {
          "field": "DATE(t.created_at)",
          "operator": "BETWEEN",
          "value": ["{{start_date}}", "{{end_date}}"],
          "logical_operator": null
        }
      ]
    },
    "group_by": ["o.id", "o.name"],
    "having": [
      {
        "field": "COUNT(*)",
        "operator": ">=",
        "value": "{{min_transactions}}"
      }
    ],
    "order_by": [
      {
        "field": "ca_solde_principal",
        "direction": "DESC"
      },
      {
        "field": "ca_credit",
        "direction": "DESC"
      }
    ],
    "parameters": {
      "profile_type": {
        "type": "enum",
        "values": ["PREPAID", "HYBRID"],
        "required": true,
        "description": "Type de profil client"
      },
      "start_date": {
        "type": "date",
        "required": true,
        "description": "Date de début"
      },
      "end_date": {
        "type": "date",
        "required": true,
        "description": "Date de fin"
      },
      "min_transactions": {
        "type": "integer",
        "required": false,
        "default": 1,
        "description": "Nombre minimum de transactions"
      }
    }
  }
}
```

### Example 3: Time-Based Revenue Analysis

```json
{
  "name": "Monthly Revenue Trends",
  "profile_type": "PREPAID",
  "balance_type": "MAIN_BALANCE",
  "section_id": "section-uuid",
  "database_table_name": ["transactions", "offers"],
  "config": {
    "select": {
      "fields": [
        {
          "name": "period",
          "expression": "DATE_FORMAT(t.created_at, '%Y-%m')",
          "alias": "periode"
        },
        {
          "name": "monthly_ca",
          "expression": "SUM(t.amount)",
          "alias": "ca_mensuel"
        },
        {
          "name": "avg_transaction",
          "expression": "AVG(t.amount)",
          "alias": "montant_moyen"
        },
        {
          "name": "unique_customers",
          "expression": "COUNT(DISTINCT t.customer_id)",
          "alias": "clients_uniques"
        }
      ]
    },
    "from": {
      "main_table": "transactions",
      "alias": "t"
    },
    "joins": [
      {
        "type": "INNER",
        "table": "offers",
        "alias": "o",
        "on": "t.offer_id = o.id AND o.is_active = 1"
      }
    ],
    "conditions": {
      "where": [
        {
          "field": "t.transaction_type",
          "operator": "=",
          "value": "PURCHASE",
          "logical_operator": "AND"
        },
        {
          "field": "t.status",
          "operator": "=",
          "value": "COMPLETED",
          "logical_operator": "AND"
        },
        {
          "field": "o.category",
          "operator": "=",
          "value": "{{offer_category}}",
          "logical_operator": "AND"
        },
        {
          "field": "t.created_at",
          "operator": ">=",
          "value": "{{start_date}}",
          "logical_operator": null
        }
      ]
    },
    "group_by": ["DATE_FORMAT(t.created_at, '%Y-%m')"],
    "order_by": [
      {
        "field": "periode",
        "direction": "ASC"
      }
    ],
    "parameters": {
      "offer_category": {
        "type": "string",
        "required": true,
        "description": "Catégorie d'offre commerciale"
      },
      "start_date": {
        "type": "date",
        "required": true,
        "description": "Date de début de la période d'analyse"
      }
    }
  }
}
```

## Best Practices

### 1. Rule Naming
- Use descriptive names that clearly indicate the rule's purpose
- Include the profile type and main metric in the name
- Example: "Prepaid Monthly Revenue Analysis", "Hybrid Balance Type CA"

### 2. Configuration Design
- **Keep it simple**: Start with basic configurations and add complexity gradually
- **Use parameters**: Make rules flexible with parameterized values
- **Validate joins**: Ensure all table joins are properly defined
- **Test conditions**: Verify WHERE clauses produce expected results

### 3. Performance Considerations
- **Index usage**: Ensure filtered columns have appropriate database indexes
- **Limit data**: Use date ranges and other filters to limit query scope
- **Aggregation efficiency**: Group by indexed columns when possible
- **Join optimization**: Use INNER JOINs when possible, LEFT JOINs when necessary

### 4. Parameter Management
- **Required vs Optional**: Mark parameters as required only when necessary
- **Default values**: Provide sensible defaults for optional parameters
- **Type validation**: Use appropriate parameter types (date, integer, enum)
- **Clear descriptions**: Write helpful parameter descriptions in French

### 5. Testing Rules
- **Start with DRAFT**: Always create rules in DRAFT status initially
- **Test with sample data**: Verify SQL generation with known datasets
- **Validate parameters**: Test with different parameter combinations
- **Performance testing**: Check query execution time with production data volumes

### 6. Rule Lifecycle
1. **DRAFT**: Initial development and testing phase
2. **ACTIVE**: Production-ready rules available for reporting
3. **INACTIVE**: Deprecated rules kept for historical reference

### 7. Error Handling
- **Validation**: The system validates configuration structure before saving
- **SQL Generation**: Test SQL generation before activating rules
- **Parameter Validation**: Ensure all required parameters are provided
- **Error Messages**: Review error responses for debugging information

## Common Patterns

### Revenue Calculation
```json
{
  "name": "total_revenue",
  "expression": "SUM(amount)",
  "alias": "chiffre_affaires"
}
```

### Customer Count
```json
{
  "name": "customer_count",
  "expression": "COUNT(DISTINCT customer_id)",
  "alias": "nombre_clients"
}
```

### Date Filtering
```json
{
  "field": "t.created_at",
  "operator": "BETWEEN",
  "value": ["{{start_date}}", "{{end_date}}"],
  "logical_operator": "AND"
}
```

### Balance Type Filtering
```json
{
  "field": "b.balance_type",
  "operator": "IN",
  "value": ["MAIN_BALANCE", "CRED"],
  "logical_operator": "AND"
}
```

### Monthly Grouping
```json
"group_by": ["DATE_FORMAT(t.created_at, '%Y-%m')"]
```

## Troubleshooting

### Common Issues

1. **Invalid Configuration**: Check JSON structure against schema
2. **Missing Parameters**: Ensure all required parameters are defined
3. **Join Errors**: Verify table relationships and join conditions
4. **SQL Generation Fails**: Review field expressions and table aliases
5. **Performance Issues**: Add appropriate WHERE clauses and indexes

### Debugging Steps

1. **Validate JSON**: Use a JSON validator to check configuration syntax
2. **Test Parameters**: Try generating SQL with sample parameter values
3. **Review Logs**: Check application logs for detailed error messages
4. **Simplify Configuration**: Start with basic config and add complexity gradually
5. **Database Schema**: Verify table and column names match your database

## Support

For additional help with rule creation:
- Review the API documentation at `/docs`
- Check the test examples in `tests/test_rule_endpoints.py`
- Examine configuration examples in `src/modules/rules/domain/models/rule_config_examples.py`
- Contact the development team for complex rule requirements
