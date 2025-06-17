# -*- coding: utf-8 -*-
# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import re

def validate_cpf(cpf):
    """
    Validate CPF (Brazilian individual taxpayer registry number)

    Args:
        cpf (str): CPF number to be validated

    Returns:
        bool: True if CPF is valid, False otherwise
    """
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

def validate_cnpj(cnpj):
    """
    Validate CNPJ (Brazilian company taxpayer registry number)

    Args:
        cnpj (str): CNPJ number to be validated

    Returns:
        bool: True if CNPJ is valid, False otherwise
    """
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

def validate_cep(cep):
    """
    Validate CEP (Brazilian postal code)

    Args:
        cep (str): CEP to be validated

    Returns:
        bool: True if CEP is valid, False otherwise
    """
    # Remove non-numeric characters
    cep = re.sub(r'[^0-9]', '', str(cep))

    # Check if CEP has 8 digits
    if len(cep) != 8:
        return False

    # Check if all digits are the same
    if cep == cep[0] * 8:
        return False

    return True
