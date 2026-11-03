---
name: feature-feedback_poclac
description: generar el reporte de feedback.
---

# Skill: Feature poclac -> Spec feedback

## 1) Metadata
- **Skill ID:** feature-feedback_poclac
- **Version:** 0.1.0
- **Purpose:** realizar el informe del feedback basado en la estructura [columnas] de los integrantes del chapter.
- **Audience (roles):** Chapter/PO, Tech Lead, líder proveedor
- **When to use:** Al termino de cada sprint de manera recurrente.
- **When NOT to use:** Durantes las ceremonias agiles: pre.work, BRP, sprint planning, sprint retrospectiva.
- **Sensitive inputs:** remuneración, antecedentes, sin sesgos inconsientes: ubicación, religión, educación, genero.
- **Expected output:** informe estructurado de acuerdo a [estructura del informe]

## 2) Inputs
Proporciona la información en este formato:

- **métricas inviduales: DR y ACCE
- **métricas de equipos: costo x pase, DF, TMD
- **Tipo de feedback: apreciativo/constructivo
- **Score de feedback: 1, 2, 3
- **Expectativas del team member
- **Accionables
- **Ejecutor del accionable
- **Transcripción de la grabación

## 3) Output
Informe en formato xls según la estructura del informe, una fila por cada team member

1. **Matricula**
2. **Nombre del team member**
3. **feedback**
4. **plan-de-accion**

## 4) Constraints
- No evaluar al tm que este con estado: fuera de oficina por 1 mes o vacaciones
- No evaluar cuando el tm no tenga al menos 1 mes en el equipo
- En caso sea proveedor no evaluar sin la participación del líder de proveedor
- En caso sea tm banco no evaluar sin la participación del LT o PO

## 5) Validation Rules
La salida es válida si:
- Se tiene feedback de todos los integrantes
- Se detalla la transcripción al informe correctamente
- Se visualizan los planes de acciones: fechas y responsables

## 6) Evidence
Muestra el informe de entrega:
- 'informe-poclac-MMYYYY' 