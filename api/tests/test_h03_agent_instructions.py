# api/tests/test_h03_agent_instructions.py
"""CA1 / tareas 2.1-2.5: contenido de las instrucciones por rol (T4, T8). Pruebas del cambio."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h03_support as s  # noqa: E402


def test_arquitectura_2_1_contratos_y_pagina_angular():
    assert not (v := s.check_required("arquitectura", s.role_text("arquitectura"))), v


def test_arquitectura_2_1_sin_api_propia():
    assert not (v := s.check_forbidden("arquitectura", s.role_text("arquitectura"))), v


def test_backend_2_2_sin_cambios_y_contrato_w2():
    assert not (v := s.check_required("backend", s.role_text("backend"))), v


def test_frontend_2_3_requisitos():
    assert not (v := s.check_required("frontend", s.role_text("frontend"))), v


def test_pruebas_2_4_navegador_mock():
    assert not (v := s.check_required("pruebas", s.role_text("pruebas"))), v


def test_pruebas_2_4_sin_comandos_inventados():
    assert not (v := s.check_forbidden("pruebas", s.role_text("pruebas"))), v


def test_seguridad_2_5_temas_requeridos():
    assert not (v := s.check_required("seguridad", s.role_text("seguridad"))), v


def test_seguridad_2_5_sin_temas_fuera_de_alcance():
    assert not (v := s.check_forbidden("seguridad", s.role_text("seguridad"))), v
