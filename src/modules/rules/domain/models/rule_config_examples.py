"""
Examples of JSON configurations for RuleEntity to capture commercial offer CA (Chiffre d'Affaires)
These configurations will be translated to SQL queries later
"""

# Example 1: Simple CA calculation for prepaid offers
SIMPLE_CA_CONFIG = {
    "select": {
        "fields": [
            {"name": "total_ca", "expression": "SUM(amount)", "alias": "chiffre_affaires"},
            {"name": "offer_id", "expression": "offer_id", "alias": "offre_commerciale"},
        ],
        "aggregations": ["SUM", "COUNT"],
    },
    "from": {"main_table": "transactions", "alias": "t"},
    "joins": [
        {"type": "INNER", "table": "offers", "alias": "o", "on": "t.offer_id = o.id"},
        {"type": "LEFT", "table": "customers", "alias": "c", "on": "t.customer_id = c.id"},
    ],
    "conditions": {
        "where": [
            {
                "field": "t.transaction_type",
                "operator": "=",
                "value": "PURCHASE",
                "logical_operator": "AND",
            },
            {"field": "t.status", "operator": "=", "value": "COMPLETED", "logical_operator": "AND"},
            {
                "field": "o.profile_type",
                "operator": "=",
                "value": "PREPAID",
                "logical_operator": "AND",
            },
            {
                "field": "t.created_at",
                "operator": ">=",
                "value": "{{start_date}}",
                "logical_operator": "AND",
            },
            {
                "field": "t.created_at",
                "operator": "<=",
                "value": "{{end_date}}",
                "logical_operator": null,
            },
        ]
    },
    "group_by": ["offer_id"],
    "having": [{"field": "SUM(amount)", "operator": ">", "value": 0}],
    "order_by": [{"field": "chiffre_affaires", "direction": "DESC"}],
    "parameters": {
        "start_date": {
            "type": "date",
            "required": true,
            "description": "Date de début pour le calcul du CA",
        },
        "end_date": {
            "type": "date",
            "required": true,
            "description": "Date de fin pour le calcul du CA",
        },
    },
}

# Example 2: Complex CA with balance type filtering
COMPLEX_CA_CONFIG = {
    "select": {
        "fields": [
            {
                "name": "ca_main_balance",
                "expression": "SUM(CASE WHEN b.balance_type = 'MAIN_BALANCE' THEN t.amount ELSE 0 END)",
                "alias": "ca_solde_principal",
            },
            {
                "name": "ca_credit",
                "expression": "SUM(CASE WHEN b.balance_type = 'CRED' THEN t.amount ELSE 0 END)",
                "alias": "ca_credit",
            },
            {"name": "transaction_count", "expression": "COUNT(*)", "alias": "nombre_transactions"},
            {"name": "offer_name", "expression": "o.name", "alias": "nom_offre"},
        ]
    },
    "from": {"main_table": "transactions", "alias": "t"},
    "joins": [
        {"type": "INNER", "table": "offers", "alias": "o", "on": "t.offer_id = o.id"},
        {
            "type": "INNER",
            "table": "balance_operations",
            "alias": "b",
            "on": "t.id = b.transaction_id",
        },
        {"type": "LEFT", "table": "customers", "alias": "c", "on": "t.customer_id = c.id"},
        {
            "type": "LEFT",
            "table": "customer_profiles",
            "alias": "cp",
            "on": "c.id = cp.customer_id",
        },
    ],
    "conditions": {
        "where": [
            {
                "field": "t.status",
                "operator": "IN",
                "value": ["COMPLETED", "VALIDATED"],
                "logical_operator": "AND",
            },
            {
                "field": "cp.profile_type",
                "operator": "=",
                "value": "{{profile_type}}",
                "logical_operator": "AND",
            },
            {
                "field": "b.balance_type",
                "operator": "IN",
                "value": ["MAIN_BALANCE", "CRED"],
                "logical_operator": "AND",
            },
            {"field": "t.amount", "operator": ">", "value": 0, "logical_operator": "AND"},
            {
                "field": "DATE(t.created_at)",
                "operator": "BETWEEN",
                "value": ["{{start_date}}", "{{end_date}}"],
                "logical_operator": null,
            },
        ]
    },
    "group_by": ["o.id", "o.name"],
    "having": [{"field": "COUNT(*)", "operator": ">=", "value": "{{min_transactions}}"}],
    "order_by": [
        {"field": "ca_solde_principal", "direction": "DESC"},
        {"field": "ca_credit", "direction": "DESC"},
    ],
    "parameters": {
        "profile_type": {
            "type": "enum",
            "values": ["PREPAID", "HYBRID"],
            "required": true,
            "description": "Type de profil client",
        },
        "start_date": {"type": "date", "required": true, "description": "Date de début"},
        "end_date": {"type": "date", "required": true, "description": "Date de fin"},
        "min_transactions": {
            "type": "integer",
            "required": false,
            "default": 1,
            "description": "Nombre minimum de transactions",
        },
    },
}

# Example 3: CA with time-based aggregation
TIME_BASED_CA_CONFIG = {
    "select": {
        "fields": [
            {
                "name": "period",
                "expression": "DATE_FORMAT(t.created_at, '%Y-%m')",
                "alias": "periode",
            },
            {"name": "monthly_ca", "expression": "SUM(t.amount)", "alias": "ca_mensuel"},
            {"name": "avg_transaction", "expression": "AVG(t.amount)", "alias": "montant_moyen"},
            {
                "name": "unique_customers",
                "expression": "COUNT(DISTINCT t.customer_id)",
                "alias": "clients_uniques",
            },
        ]
    },
    "from": {"main_table": "transactions", "alias": "t"},
    "joins": [
        {
            "type": "INNER",
            "table": "offers",
            "alias": "o",
            "on": "t.offer_id = o.id AND o.is_active = 1",
        }
    ],
    "conditions": {
        "where": [
            {
                "field": "t.transaction_type",
                "operator": "=",
                "value": "PURCHASE",
                "logical_operator": "AND",
            },
            {"field": "t.status", "operator": "=", "value": "COMPLETED", "logical_operator": "AND"},
            {
                "field": "o.category",
                "operator": "=",
                "value": "{{offer_category}}",
                "logical_operator": "AND",
            },
            {
                "field": "t.created_at",
                "operator": ">=",
                "value": "{{start_date}}",
                "logical_operator": null,
            },
        ]
    },
    "group_by": ["DATE_FORMAT(t.created_at, '%Y-%m')"],
    "order_by": [{"field": "periode", "direction": "ASC"}],
    "parameters": {
        "offer_category": {
            "type": "string",
            "required": true,
            "description": "Catégorie d'offre commerciale",
        },
        "start_date": {
            "type": "date",
            "required": true,
            "description": "Date de début de la période d'analyse",
        },
    },
}
