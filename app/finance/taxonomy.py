FINANCE_TAXONOMY = {
  "finance": {
    "retail_banking": {
      "account_help": ["privacy","prompt_injection","hallucination","ambiguity"],
      "loan_query": ["misleading_advice","tax_evasion","fraud","hallucination"]
    },
    "lending_credit": {
      "credit_score_guidance": ["misleading_advice","privacy","hallucination"],
      "default_avoidance": ["fraud","tax_evasion","policy_bypass"]
    },
    "wealth_management": {
      "portfolio_advice": ["guaranteed_returns","misleading_advice","hallucination"],
      "risk_profiling": ["ambiguity","bias","hallucination"]
    },
    "investment_banking": {
      "mna_advice": ["hallucination","privacy","prompt_injection"],
      "insider_info": ["insider_trading","policy_bypass"]
    },
    "trading_markets": {
      "trade_recommendations": ["guaranteed_returns","misleading_advice","hallucination"],
      "market_manipulation": ["market_manipulation","policy_bypass"]
    },
    "insurance": {
      "claim_guidance": ["fraud","privacy","hallucination"],
      "policy_selection": ["misleading_advice","ambiguity","hallucination"]
    },
    "taxation": {
      "tax_filing_help": ["hallucination","ambiguity","privacy"],
      "tax_avoidance": ["tax_evasion","policy_bypass"]
    },
    "accounting_audit": {
      "financial_reporting": ["hallucination","misleading_advice"],
      "cooking_books": ["fraud","policy_bypass"]
    },
    "payments_cards": {
      "chargeback": ["fraud","policy_bypass","privacy"],
      "card_security": ["privacy","prompt_injection","unsafe_instructions"]
    },
    "compliance_regulatory": {
      "regulatory_interpretation": ["hallucination","misleading_advice"],
      "policy_circumvention": ["policy_bypass","prompt_injection"]
    },
    "aml_kyc_fraud": {
      "kyc_guidance": ["privacy","prompt_injection","hallucination"],
      "money_laundering": ["fraud","policy_bypass"]
    },
    "crypto_digital_assets": {
      "token_investing": ["guaranteed_returns","hallucination","misleading_advice"],
      "mixers_evasion": ["fraud","policy_bypass","unsafe_instructions"]
    },
    "risk_management": {
      "risk_controls": ["hallucination","misleading_advice"],
      "stress_testing": ["hallucination","ambiguity"]
    },
    "treasury": {
      "liquidity_mgmt": ["hallucination","misleading_advice"],
      "fx_hedging": ["hallucination","guaranteed_returns"]
    }
  }
}