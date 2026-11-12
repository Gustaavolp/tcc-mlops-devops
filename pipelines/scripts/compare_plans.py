#!/usr/bin/env python3
"""Compara dois planos Terraform (saída de `terraform show -json`).

Sai com código 0 se ambos propõem as mesmas ações sobre os mesmos recursos e
com código 1 caso contrário, listando as diferenças. Usado pelo pipeline de
infraestrutura para garantir que o plano aplicado é o mesmo que foi aprovado.
"""
import json
import sys


def actions(path):
    with open(path, encoding="utf-8") as fh:
        plan = json.load(fh)
    result = {}
    for rc in plan.get("resource_changes", []):
        acts = tuple(rc["change"]["actions"])
        if acts != ("no-op",):
            result[rc["address"]] = acts
    return result


def main(approved_path, current_path):
    approved, current = actions(approved_path), actions(current_path)
    if approved == current:
        print(f"plano inalterado ({len(current)} recurso(s) com alterações)")
        return 0
    for addr in sorted(set(approved) | set(current)):
        a, c = approved.get(addr), current.get(addr)
        if a != c:
            print(f"  {addr}: aprovado={a} atual={c}")
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("uso: compare_plans.py <aprovado.json> <atual.json>")
    sys.exit(main(sys.argv[1], sys.argv[2]))
