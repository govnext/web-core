# -*- coding: utf-8 -*-
# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json

@frappe.whitelist()
def get_government_units():
    """
    Retorna todas as unidades governamentais
    """
    try:
        units = frappe.get_all("Government Unit",
                              fields=["name", "unit_name", "unit_type", "parent_unit", "is_active"],
                              filters={"is_active": 1})
        return {"data": units}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API Error: Get Government Units")
        return {"error": str(e)}

@frappe.whitelist()
def get_public_budgets(government_unit=None, year=None):
    """
    Retorna orçamentos públicos filtrados por unidade governamental e/ou ano
    """
    try:
        filters = {}
        if government_unit:
            filters["government_unit"] = government_unit
        if year:
            filters["fiscal_year"] = year

        budgets = frappe.get_all("Public Budget",
                                fields=["name", "government_unit", "fiscal_year", "total_revenue",
                                       "total_expenses", "status", "creation", "modified"],
                                filters=filters)
        return {"data": budgets}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API Error: Get Public Budgets")
        return {"error": str(e)}

@frappe.whitelist()
def get_public_tenders(government_unit=None, status=None):
    """
    Retorna licitações públicas filtradas por unidade governamental e/ou status
    """
    try:
        filters = {}
        if government_unit:
            filters["government_unit"] = government_unit
        if status:
            filters["status"] = status

        tenders = frappe.get_all("Public Tender",
                               fields=["name", "tender_title", "government_unit", "tender_type",
                                      "start_date", "end_date", "status", "total_value"],
                               filters=filters)
        return {"data": tenders}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API Error: Get Public Tenders")
        return {"error": str(e)}
