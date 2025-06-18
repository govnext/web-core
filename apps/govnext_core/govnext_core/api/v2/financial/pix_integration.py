# -*- coding: utf-8 -*-
# Copyright (c) 2024, GovNext Team and contributors
# For license information, please see license.txt

import frappe
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import base64
import hashlib
import hmac
from frappe import _
from frappe.utils import now_datetime, flt, cstr
import uuid


class PIXIntegration:
    """
    Integração completa com PIX para municípios
    
    Funcionalidades:
    - Criação de cobranças PIX
    - Webhook para recebimento de pagamentos
    - Conciliação automática
    - Estorno de pagamentos
    - QR Code dinâmico
    - Consulta de transações
    """
    
    def __init__(self):
        self.settings = self._get_pix_settings()
        self.api_base_url = self.settings.get("api_base_url", "https://api.bb.com.br/pix/v1")
        self.client_id = self.settings.get("client_id")
        self.client_secret = self.settings.get("client_secret")
        self.certificate_path = self.settings.get("certificate_path")
        self.private_key_path = self.settings.get("private_key_path")
        self.webhook_secret = self.settings.get("webhook_secret")
        self.access_token = None
        self.token_expires_at = None
    
    def _get_pix_settings(self) -> Dict:
        """Obtém configurações PIX do sistema"""
        try:
            settings = frappe.get_single("PIX Settings")
            return settings.as_dict()
        except Exception:
            return {}
    
    def authenticate(self) -> bool:
        """
        Autentica com a API PIX do banco
        
        Returns:
            True se autenticação bem-sucedida
        """
        try:
            # Verificar se token ainda é válido
            if self.access_token and self.token_expires_at:
                if datetime.now() < self.token_expires_at:
                    return True
            
            # Autenticar usando OAuth2 com certificado digital
            auth_url = f"{self.api_base_url}/oauth/token"
            
            auth_string = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
            
            headers = {
                "Authorization": f"Basic {auth_string}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "client_credentials",
                "scope": "pix.read pix.write"
            }
            
            # Usar certificado digital para autenticação mTLS
            cert = (self.certificate_path, self.private_key_path) if self.certificate_path else None
            
            response = requests.post(
                auth_url,
                headers=headers,
                data=data,
                cert=cert,
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
                
                return True
            else:
                frappe.log_error(f"Erro na autenticação PIX: {response.text}", "PIX Authentication Error")
                return False
                
        except Exception as e:
            frappe.log_error(f"Erro na autenticação PIX: {str(e)}", "PIX Authentication Error")
            return False
    
    def create_charge(self, amount: float, description: str, taxpayer_id: str = None,
                     due_date: datetime = None, additional_info: Dict = None) -> Dict:
        """
        Cria cobrança PIX
        
        Args:
            amount: Valor da cobrança
            description: Descrição da cobrança
            taxpayer_id: CPF/CNPJ do pagador
            due_date: Data de vencimento
            additional_info: Informações adicionais
            
        Returns:
            Dict com dados da cobrança criada
        """
        try:
            if not self.authenticate():
                frappe.throw(_("Erro na autenticação com o sistema PIX"))
            
            # Gerar ID único para a transação
            txid = f"GN{uuid.uuid4().hex[:25].upper()}"
            
            # Preparar payload da cobrança
            charge_data = {
                "calendario": {
                    "expiracao": 3600  # 1 hora por padrão
                },
                "valor": {
                    "original": f"{amount:.2f}"
                },
                "chave": self.settings.get("pix_key"),  # Chave PIX do município
                "solicitacaoPagador": description[:140]  # Limite de 140 caracteres
            }
            
            # Adicionar data de vencimento se fornecida
            if due_date:
                charge_data["calendario"]["dataDeVencimento"] = due_date.strftime("%Y-%m-%d")
                charge_data["calendario"]["validadeAposVencimento"] = 30  # 30 dias após vencimento
            
            # Adicionar informações do pagador se fornecidas
            if taxpayer_id:
                if len(taxpayer_id) == 11:  # CPF
                    charge_data["devedor"] = {
                        "cpf": taxpayer_id,
                        "nome": additional_info.get("payer_name", "Contribuinte") if additional_info else "Contribuinte"
                    }
                else:  # CNPJ
                    charge_data["devedor"] = {
                        "cnpj": taxpayer_id,
                        "nome": additional_info.get("payer_name", "Empresa") if additional_info else "Empresa"
                    }
            
            # Adicionar informações adicionais
            if additional_info:
                info_adicional = []
                for key, value in additional_info.items():
                    if key not in ["payer_name"] and len(info_adicional) < 50:  # Limite de 50 campos
                        info_adicional.append({
                            "nome": key[:50],  # Máximo 50 caracteres
                            "valor": str(value)[:200]  # Máximo 200 caracteres
                        })
                
                if info_adicional:
                    charge_data["infoAdicionais"] = info_adicional
            
            # Fazer requisição para criar cobrança
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            cert = (self.certificate_path, self.private_key_path) if self.certificate_path else None
            
            response = requests.put(
                f"{self.api_base_url}/cob/{txid}",
                headers=headers,
                json=charge_data,
                cert=cert,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                charge_response = response.json()
                
                # Salvar cobrança no banco de dados
                charge_doc = frappe.get_doc({
                    "doctype": "PIX Charge",
                    "txid": txid,
                    "amount": amount,
                    "description": description,
                    "taxpayer_id": taxpayer_id,
                    "due_date": due_date,
                    "status": charge_response.get("status", "ATIVA"),
                    "location": charge_response.get("location"),
                    "pix_copy_paste": charge_response.get("pixCopiaECola"),
                    "qr_code": charge_response.get("qrcode"),
                    "creation_date": now_datetime(),
                    "additional_info": json.dumps(additional_info) if additional_info else None
                })
                charge_doc.insert(ignore_permissions=True)
                frappe.db.commit()
                
                return {
                    "success": True,
                    "txid": txid,
                    "amount": amount,
                    "status": charge_response.get("status"),
                    "pix_copy_paste": charge_response.get("pixCopiaECola"),
                    "qr_code": charge_response.get("qrcode"),
                    "location": charge_response.get("location"),
                    "expires_at": charge_response.get("calendario", {}).get("criacao")
                }
            else:
                error_msg = f"Erro ao criar cobrança PIX: {response.status_code} - {response.text}"
                frappe.log_error(error_msg, "PIX Charge Creation Error")
                frappe.throw(_(error_msg))
                
        except Exception as e:
            frappe.log_error(f"Erro ao criar cobrança PIX: {str(e)}", "PIX Charge Creation Error")
            frappe.throw(_("Erro interno ao criar cobrança PIX"))
    
    def get_charge_status(self, txid: str) -> Dict:
        """
        Consulta status de uma cobrança PIX
        
        Args:
            txid: ID da transação
            
        Returns:
            Dict com status da cobrança
        """
        try:
            if not self.authenticate():
                frappe.throw(_("Erro na autenticação com o sistema PIX"))
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            cert = (self.certificate_path, self.private_key_path) if self.certificate_path else None
            
            response = requests.get(
                f"{self.api_base_url}/cob/{txid}",
                headers=headers,
                cert=cert,
                timeout=30
            )
            
            if response.status_code == 200:
                charge_data = response.json()
                
                # Atualizar status no banco
                if frappe.db.exists("PIX Charge", {"txid": txid}):
                    frappe.db.set_value("PIX Charge", {"txid": txid}, {
                        "status": charge_data.get("status"),
                        "last_update": now_datetime()
                    })
                    frappe.db.commit()
                
                return {
                    "success": True,
                    "txid": txid,
                    "status": charge_data.get("status"),
                    "amount": charge_data.get("valor", {}).get("original"),
                    "paid_amount": charge_data.get("valor", {}).get("liquidacao"),
                    "creation_date": charge_data.get("calendario", {}).get("criacao"),
                    "payment_date": charge_data.get("pix", [{}])[0].get("horario") if charge_data.get("pix") else None
                }
            else:
                error_msg = f"Erro ao consultar cobrança PIX: {response.status_code} - {response.text}"
                frappe.log_error(error_msg, "PIX Charge Query Error")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            frappe.log_error(f"Erro ao consultar cobrança PIX: {str(e)}", "PIX Charge Query Error")
            return {"success": False, "error": str(e)}
    
    def process_webhook(self, payload: Dict, signature: str = None) -> Dict:
        """
        Processa webhook de pagamento PIX recebido
        
        Args:
            payload: Dados do webhook
            signature: Assinatura para validação
            
        Returns:
            Dict com resultado do processamento
        """
        try:
            # Validar assinatura do webhook se configurada
            if self.webhook_secret and signature:
                if not self._validate_webhook_signature(json.dumps(payload), signature):
                    frappe.log_error("Assinatura inválida no webhook PIX", "PIX Webhook Security Error")
                    return {"success": False, "error": "Assinatura inválida"}
            
            # Processar cada PIX recebido
            processed_payments = []
            
            for pix_data in payload.get("pix", []):
                result = self._process_pix_payment(pix_data)
                processed_payments.append(result)
            
            # Log do webhook recebido
            frappe.get_doc({
                "doctype": "PIX Webhook Log",
                "payload": json.dumps(payload),
                "signature": signature,
                "processed_at": now_datetime(),
                "processed_count": len(processed_payments),
                "success_count": sum(1 for p in processed_payments if p.get("success"))
            }).insert(ignore_permissions=True)
            
            frappe.db.commit()
            
            return {
                "success": True,
                "processed_payments": processed_payments,
                "total_processed": len(processed_payments)
            }
            
        except Exception as e:
            frappe.log_error(f"Erro no processamento do webhook PIX: {str(e)}", "PIX Webhook Error")
            return {"success": False, "error": str(e)}
    
    def _process_pix_payment(self, pix_data: Dict) -> Dict:
        """Processa um pagamento PIX individual"""
        try:
            end_to_end_id = pix_data.get("endToEndId")
            txid = pix_data.get("txid")
            amount = flt(pix_data.get("valor", 0))
            payment_date = pix_data.get("horario")
            
            # Verificar se pagamento já foi processado
            if frappe.db.exists("PIX Payment", {"end_to_end_id": end_to_end_id}):
                return {"success": True, "message": "Pagamento já processado", "end_to_end_id": end_to_end_id}
            
            # Criar registro de pagamento
            payment_doc = frappe.get_doc({
                "doctype": "PIX Payment",
                "end_to_end_id": end_to_end_id,
                "txid": txid,
                "amount": amount,
                "payment_date": payment_date,
                "payer_name": pix_data.get("pagador", {}).get("nome"),
                "payer_document": pix_data.get("pagador", {}).get("cpf") or pix_data.get("pagador", {}).get("cnpj"),
                "payer_bank": pix_data.get("pagador", {}).get("banco"),
                "raw_data": json.dumps(pix_data),
                "status": "Received",
                "processed_at": now_datetime()
            })
            payment_doc.insert(ignore_permissions=True)
            
            # Atualizar cobrança se existir
            if txid and frappe.db.exists("PIX Charge", {"txid": txid}):
                frappe.db.set_value("PIX Charge", {"txid": txid}, {
                    "status": "CONCLUIDA",
                    "paid_amount": amount,
                    "payment_date": payment_date,
                    "end_to_end_id": end_to_end_id
                })
            
            # Executar conciliação automática
            self._auto_reconcile_payment(payment_doc)
            
            frappe.db.commit()
            
            return {
                "success": True,
                "end_to_end_id": end_to_end_id,
                "amount": amount,
                "message": "Pagamento processado com sucesso"
            }
            
        except Exception as e:
            frappe.log_error(f"Erro ao processar pagamento PIX: {str(e)}", "PIX Payment Processing Error")
            return {"success": False, "error": str(e)}
    
    def _auto_reconcile_payment(self, payment_doc):
        """Executa conciliação automática do pagamento"""
        try:
            # Buscar cobrança relacionada
            if payment_doc.txid:
                charge = frappe.get_doc("PIX Charge", {"txid": payment_doc.txid})
                
                # Criar entrada no diário financeiro
                journal_entry = frappe.get_doc({
                    "doctype": "Journal Entry",
                    "voucher_type": "Journal Entry",
                    "posting_date": payment_doc.payment_date,
                    "company": frappe.defaults.get_defaults().get("company"),
                    "accounts": [
                        {
                            "account": self.settings.get("pix_receipt_account"),
                            "debit_in_account_currency": payment_doc.amount,
                            "reference_type": "PIX Payment",
                            "reference_name": payment_doc.name
                        },
                        {
                            "account": self.settings.get("pix_clearing_account"),
                            "credit_in_account_currency": payment_doc.amount,
                            "reference_type": "PIX Payment",
                            "reference_name": payment_doc.name
                        }
                    ],
                    "user_remark": f"Recebimento PIX - {payment_doc.end_to_end_id}"
                })
                journal_entry.insert(ignore_permissions=True)
                journal_entry.submit()
                
                # Atualizar status do pagamento
                payment_doc.db_set("reconciliation_status", "Reconciled")
                payment_doc.db_set("journal_entry", journal_entry.name)
                
        except Exception as e:
            frappe.log_error(f"Erro na conciliação automática: {str(e)}", "PIX Auto Reconciliation Error")
    
    def _validate_webhook_signature(self, payload: str, signature: str) -> bool:
        """Valida assinatura do webhook"""
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception:
            return False
    
    def refund_payment(self, end_to_end_id: str, amount: Optional[float] = None, 
                      reason: str = None) -> Dict:
        """
        Solicita estorno de pagamento PIX
        
        Args:
            end_to_end_id: ID end-to-end do pagamento original
            amount: Valor do estorno (opcional, padrão é valor total)
            reason: Motivo do estorno
            
        Returns:
            Dict com resultado da solicitação
        """
        try:
            if not self.authenticate():
                frappe.throw(_("Erro na autenticação com o sistema PIX"))
            
            # Buscar pagamento original
            payment = frappe.get_doc("PIX Payment", {"end_to_end_id": end_to_end_id})
            
            refund_amount = amount or payment.amount
            refund_id = f"D{uuid.uuid4().hex[:34].upper()}"
            
            refund_data = {
                "valor": f"{refund_amount:.2f}",
                "natureza": "DEVOLUCAO",
                "descricao": reason or "Estorno solicitado pelo município"[:140]
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            cert = (self.certificate_path, self.private_key_path) if self.certificate_path else None
            
            response = requests.put(
                f"{self.api_base_url}/pix/{end_to_end_id}/devolucao/{refund_id}",
                headers=headers,
                json=refund_data,
                cert=cert,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                refund_response = response.json()
                
                # Criar registro de estorno
                refund_doc = frappe.get_doc({
                    "doctype": "PIX Refund",
                    "original_payment": payment.name,
                    "end_to_end_id": end_to_end_id,
                    "refund_id": refund_id,
                    "amount": refund_amount,
                    "reason": reason,
                    "status": refund_response.get("status", "SOLICITADA"),
                    "requested_at": now_datetime(),
                    "raw_response": json.dumps(refund_response)
                })
                refund_doc.insert(ignore_permissions=True)
                frappe.db.commit()
                
                return {
                    "success": True,
                    "refund_id": refund_id,
                    "status": refund_response.get("status"),
                    "amount": refund_amount
                }
            else:
                error_msg = f"Erro ao solicitar estorno PIX: {response.status_code} - {response.text}"
                frappe.log_error(error_msg, "PIX Refund Error")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            frappe.log_error(f"Erro ao solicitar estorno PIX: {str(e)}", "PIX Refund Error")
            return {"success": False, "error": str(e)}
    
    def get_transactions(self, start_date: datetime, end_date: datetime = None) -> List[Dict]:
        """
        Consulta transações PIX em período
        
        Args:
            start_date: Data inicial
            end_date: Data final (padrão é hoje)
            
        Returns:
            Lista de transações
        """
        try:
            if not self.authenticate():
                frappe.throw(_("Erro na autenticação com o sistema PIX"))
            
            if not end_date:
                end_date = datetime.now()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "inicio": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "fim": end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            
            cert = (self.certificate_path, self.private_key_path) if self.certificate_path else None
            
            response = requests.get(
                f"{self.api_base_url}/pix",
                headers=headers,
                params=params,
                cert=cert,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("pix", [])
            else:
                frappe.log_error(f"Erro ao consultar transações PIX: {response.text}", "PIX Query Error")
                return []
                
        except Exception as e:
            frappe.log_error(f"Erro ao consultar transações PIX: {str(e)}", "PIX Query Error")
            return []


# Instância global da integração PIX
pix_integration = PIXIntegration()