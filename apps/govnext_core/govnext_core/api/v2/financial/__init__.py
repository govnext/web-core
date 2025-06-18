# -*- coding: utf-8 -*-
# Copyright (c) 2024, GovNext Team and contributors
# For license information, please see license.txt

"""
Módulo Financeiro API v2.0
==========================

Integração com sistemas bancários e de pagamento:
- PIX: Cobrança, recebimento, webhook
- Banco do Brasil: Saldo, extrato, transferências
- Conciliação automática
- Gestão de receitas e despesas
- Relatórios financeiros
"""

from .pix_integration import PIXIntegration
from .banking_service import BankingService
from .reconciliation import FinancialReconciliation
from .treasury_management import TreasuryManagement

__all__ = ["PIXIntegration", "BankingService", "FinancialReconciliation", "TreasuryManagement"]