# -*- coding: utf-8 -*-
# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import re
import frappe
from frappe import _
from datetime import datetime, date
import json
from decimal import Decimal, InvalidOperation

class GovNextValidator:
    """
    Sistema de Validação Governamental
    Implementa validações específicas para o setor público brasileiro
    """
    
    @staticmethod
    def validate_cpf(cpf):
        """
        Validate CPF (Brazilian individual taxpayer registry number)

        Args:
            cpf (str): CPF number to be validated

        Returns:
            bool: True if CPF is valid, False otherwise
        """
        if not cpf:
            return False
            
        # Remove non-numeric characters
        cpf = re.sub(r'[^0-9]', '', str(cpf))

        # Check if CPF has 11 digits
        if len(cpf) != 11:
            return False

        # Check if all digits are the same
        if cpf == cpf[0] * 11:
            return False

        # Validate first verification digit
        sum_of_products = 0
        for i in range(9):
            sum_of_products += int(cpf[i]) * (10 - i)

        expected_digit = (sum_of_products * 10) % 11
        if expected_digit == 10:
            expected_digit = 0

        if int(cpf[9]) != expected_digit:
            return False

        # Validate second verification digit
        sum_of_products = 0
        for i in range(10):
            sum_of_products += int(cpf[i]) * (11 - i)

        expected_digit = (sum_of_products * 10) % 11
        if expected_digit == 10:
            expected_digit = 0

        if int(cpf[10]) != expected_digit:
            return False

        return True

    @staticmethod
    def validate_cnpj(cnpj):
        """
        Validate CNPJ (Brazilian company taxpayer registry number)

        Args:
            cnpj (str): CNPJ number to be validated

        Returns:
            bool: True if CNPJ is valid, False otherwise
        """
        if not cnpj:
            return False
            
        # Remove non-numeric characters
        cnpj = re.sub(r'[^0-9]', '', str(cnpj))

        # Check if CNPJ has 14 digits
        if len(cnpj) != 14:
            return False

        # Check if all digits are the same
        if cnpj == cnpj[0] * 14:
            return False

        # Validate first verification digit
        weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum_of_products = 0

        for i in range(12):
            sum_of_products += int(cnpj[i]) * weights[i]

        expected_digit = sum_of_products % 11
        if expected_digit < 2:
            expected_digit = 0
        else:
            expected_digit = 11 - expected_digit

        if int(cnpj[12]) != expected_digit:
            return False

        # Validate second verification digit
        weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum_of_products = 0

        for i in range(13):
            sum_of_products += int(cnpj[i]) * weights[i]

        expected_digit = sum_of_products % 11
        if expected_digit < 2:
            expected_digit = 0
        else:
            expected_digit = 11 - expected_digit

        if int(cnpj[13]) != expected_digit:
            return False

        return True

    @staticmethod
    def validate_cep(cep):
        """
        Validate CEP (Brazilian postal code)

        Args:
            cep (str): CEP to be validated

        Returns:
            bool: True if CEP is valid, False otherwise
        """
        if not cep:
            return False
            
        # Remove non-numeric characters
        cep = re.sub(r'[^0-9]', '', str(cep))

        # Check if CEP has 8 digits
        if len(cep) != 8:
            return False

        # Check if all digits are the same
        if cep == cep[0] * 8:
            return False

        return True
    
    @staticmethod
    def validate_pis_pasep(pis):
        """
        Validate PIS/PASEP number
        
        Args:
            pis (str): PIS/PASEP number
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not pis:
            return False
            
        # Remove non-numeric characters
        pis = re.sub(r'[^0-9]', '', str(pis))
        
        # Check if has 11 digits
        if len(pis) != 11:
            return False
        
        # Check if all digits are the same
        if pis == pis[0] * 11:
            return False
        
        # Validate verification digit
        weights = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum_of_products = 0
        
        for i in range(10):
            sum_of_products += int(pis[i]) * weights[i]
        
        remainder = sum_of_products % 11
        
        if remainder < 2:
            expected_digit = 0
        else:
            expected_digit = 11 - remainder
        
        return int(pis[10]) == expected_digit
    
    @staticmethod
    def validate_titulo_eleitor(titulo):
        """
        Validate Título de Eleitor (Voter Registration)
        
        Args:
            titulo (str): Título de eleitor number
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not titulo:
            return False
            
        # Remove non-numeric characters
        titulo = re.sub(r'[^0-9]', '', str(titulo))
        
        # Check if has 12 digits
        if len(titulo) != 12:
            return False
        
        # Split into parts
        sequence = titulo[:8]
        state_code = titulo[8:10]
        verification = titulo[10:12]
        
        # Validate state code
        if int(state_code) == 0 or int(state_code) > 23:
            return False
        
        # Validate first verification digit
        weights = [2, 3, 4, 5, 6, 7, 8, 9]
        sum_of_products = 0
        
        for i in range(8):
            sum_of_products += int(sequence[i]) * weights[i]
        
        remainder = sum_of_products % 11
        first_digit = 0 if remainder < 2 else 11 - remainder
        
        if int(verification[0]) != first_digit:
            return False
        
        # Validate second verification digit
        state_first_digit = sum(int(d) * w for d, w in zip(state_code, [7, 8]))
        state_first_digit += first_digit * 9
        
        remainder = state_first_digit % 11
        second_digit = 0 if remainder < 2 else 11 - remainder
        
        return int(verification[1]) == second_digit
    
    @staticmethod
    def validate_email(email):
        """
        Validate email address
        
        Args:
            email (str): Email address
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not email:
            return False
            
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone):
        """
        Validate Brazilian phone number
        
        Args:
            phone (str): Phone number
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not phone:
            return False
            
        # Remove non-numeric characters
        phone = re.sub(r'[^0-9]', '', str(phone))
        
        # Check length (10 or 11 digits for mobile)
        if len(phone) not in [10, 11]:
            return False
        
        # Check area code (first 2 digits)
        area_code = int(phone[:2])
        if area_code < 11 or area_code > 99:
            return False
        
        return True
    
    @staticmethod
    def validate_currency(value):
        """
        Validate currency value
        
        Args:
            value: Currency value
            
        Returns:
            bool: True if valid, False otherwise
        """
        if value is None:
            return False
            
        try:
            decimal_value = Decimal(str(value))
            return decimal_value >= 0
        except (InvalidOperation, ValueError):
            return False
    
    @staticmethod
    def validate_date(date_str, date_format="%Y-%m-%d"):
        """
        Validate date string
        
        Args:
            date_str (str): Date string
            date_format (str): Expected date format
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not date_str:
            return False
            
        try:
            datetime.strptime(date_str, date_format)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_government_level(level):
        """
        Validate government level
        
        Args:
            level (str): Government level
            
        Returns:
            bool: True if valid, False otherwise
        """
        valid_levels = ['federal', 'estadual', 'municipal']
        return level in valid_levels
    
    @staticmethod
    def validate_tender_type(tender_type):
        """
        Validate tender type according to Brazilian law
        
        Args:
            tender_type (str): Tender type
            
        Returns:
            bool: True if valid, False otherwise
        """
        valid_types = [
            'Concorrência',
            'Tomada de Preços',
            'Convite',
            'Concurso',
            'Leilão',
            'Pregão Eletrônico',
            'Pregão Presencial',
            'Registro de Preços',
            'Dispensa',
            'Inexigibilidade'
        ]
        return tender_type in valid_types
    
    @staticmethod
    def validate_budget_category(category):
        """
        Validate budget category
        
        Args:
            category (str): Budget category
            
        Returns:
            bool: True if valid, False otherwise
        """
        valid_categories = [
            'Receitas Correntes',
            'Receitas de Capital',
            'Despesas Correntes',
            'Despesas de Capital',
            'Reserva de Contingência'
        ]
        return category in valid_categories

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def validate_document_data(doctype, data, ignore_mandatory=False):
    """
    Validate document data against DocType meta
    
    Args:
        doctype (str): DocType name
        data (dict): Data to validate
        ignore_mandatory (bool): Skip mandatory field validation
        
    Returns:
        dict: Validation results
    """
    try:
        meta = frappe.get_meta(doctype)
        errors = []
        warnings = []
        
        # Check mandatory fields
        if not ignore_mandatory:
            for field in meta.get_mandatory_fields():
                if field.fieldname not in data or not data[field.fieldname]:
                    errors.append(f"Campo obrigatório ausente: {field.label or field.fieldname}")
        
        # Validate field types and values
        for field in meta.fields:
            if field.fieldname in data:
                value = data[field.fieldname]
                
                # Skip empty values for non-mandatory fields
                if not value and field.reqd != 1:
                    continue
                
                # Type-specific validations
                if field.fieldtype == 'Email':
                    if not GovNextValidator.validate_email(value):
                        errors.append(f"Email inválido: {field.label or field.fieldname}")
                
                elif field.fieldtype == 'Phone':
                    if not GovNextValidator.validate_phone(value):
                        errors.append(f"Telefone inválido: {field.label or field.fieldname}")
                
                elif field.fieldtype == 'Date':
                    if not GovNextValidator.validate_date(str(value)):
                        errors.append(f"Data inválida: {field.label or field.fieldname}")
                
                elif field.fieldtype == 'Currency':
                    if not GovNextValidator.validate_currency(value):
                        errors.append(f"Valor monetário inválido: {field.label or field.fieldname}")
                
                # Custom validations for government-specific fields
                if field.fieldname == 'cpf':
                    if not GovNextValidator.validate_cpf(value):
                        errors.append("CPF inválido")
                
                elif field.fieldname == 'cnpj':
                    if not GovNextValidator.validate_cnpj(value):
                        errors.append("CNPJ inválido")
                
                elif field.fieldname == 'cep':
                    if not GovNextValidator.validate_cep(value):
                        errors.append("CEP inválido")
                
                elif field.fieldname == 'pis_pasep':
                    if not GovNextValidator.validate_pis_pasep(value):
                        errors.append("PIS/PASEP inválido")
                
                elif field.fieldname == 'titulo_eleitor':
                    if not GovNextValidator.validate_titulo_eleitor(value):
                        errors.append("Título de eleitor inválido")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Document Validation Error")
        return {
            "valid": False,
            "errors": [f"Erro na validação: {str(e)}"],
            "warnings": []
        }

def sanitize_input(data, allowed_fields=None):
    """
    Sanitize input data
    
    Args:
        data (dict): Input data
        allowed_fields (list): List of allowed field names
        
    Returns:
        dict: Sanitized data
    """
    if not isinstance(data, dict):
        return {}
    
    sanitized = {}
    
    for key, value in data.items():
        # Skip if field not in allowed list
        if allowed_fields and key not in allowed_fields:
            continue
        
        # Sanitize key
        clean_key = re.sub(r'[^a-zA-Z0-9_]', '', str(key))
        
        # Sanitize value based on type
        if isinstance(value, str):
            # Remove potentially dangerous characters
            clean_value = re.sub(r'[<>"\']', '', value)
            # Limit length
            clean_value = clean_value[:1000]
        elif isinstance(value, (int, float)):
            clean_value = value
        elif isinstance(value, (list, dict)):
            # Convert to JSON string and limit size
            json_str = json.dumps(value)[:5000]
            try:
                clean_value = json.loads(json_str)
            except:
                clean_value = str(value)[:1000]
        else:
            clean_value = str(value)[:1000]
        
        sanitized[clean_key] = clean_value
    
    return sanitized

def validate_api_input(schema):
    """
    Decorator for API input validation
    
    Args:
        schema (dict): Validation schema
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            data = frappe.local.form_dict
            
            # Required fields
            for field in schema.get('required', []):
                if field not in data or not data[field]:
                    frappe.throw(_("Campo obrigatório: {0}").format(field))
            
            # Field types
            for field, field_type in schema.get('types', {}).items():
                if field in data and data[field]:
                    value = data[field]
                    
                    if field_type == 'email':
                        if not GovNextValidator.validate_email(value):
                            frappe.throw(_("Email inválido: {0}").format(field))
                    
                    elif field_type == 'phone':
                        if not GovNextValidator.validate_phone(value):
                            frappe.throw(_("Telefone inválido: {0}").format(field))
                    
                    elif field_type == 'cpf':
                        if not GovNextValidator.validate_cpf(value):
                            frappe.throw(_("CPF inválido: {0}").format(field))
                    
                    elif field_type == 'cnpj':
                        if not GovNextValidator.validate_cnpj(value):
                            frappe.throw(_("CNPJ inválido: {0}").format(field))
                    
                    elif field_type == 'currency':
                        if not GovNextValidator.validate_currency(value):
                            frappe.throw(_("Valor monetário inválido: {0}").format(field))
                    
                    elif field_type == 'date':
                        if not GovNextValidator.validate_date(value):
                            frappe.throw(_("Data inválida: {0}").format(field))
            
            # Custom validations
            for field, validation_func in schema.get('custom', {}).items():
                if field in data and data[field]:
                    if not validation_func(data[field]):
                        frappe.throw(_("Valor inválido para {0}").format(field))
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Backward compatibility
validate_cpf = GovNextValidator.validate_cpf
validate_cnpj = GovNextValidator.validate_cnpj
validate_cep = GovNextValidator.validate_cep
