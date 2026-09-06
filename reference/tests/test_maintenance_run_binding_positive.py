"""Positive PAMA binding cases for maintenance-run evidence."""

import unittest

from agentmem_ref.maintenance_run import validate_run
from tests._maintenance_run_cases import pama_decision, run_record


class MaintenanceRunBindingPositiveTests(unittest.TestCase):
    def test_exact_binding(self):
        ref, document, item = pama_decision("promotion", risk="low")
        record = run_record(constituent_decisions=(item,))
        validate_run(record, {ref: document})

    def test_pama_1_2_operation_is_preserved(self):
        ref, document, item = pama_decision("domain_schema_mutation", risk="low", reviewed=True)
        record = run_record(
            run_id="run:schema",
            planned_operations=("domain_schema_mutation",),
            constituent_decisions=(item,),
        )
        validate_run(record, {ref: document})
        self.assertEqual(document["schema_version"], "1.2.0")
        self.assertEqual(item["operation"], "domain_schema_mutation")


if __name__ == "__main__":
    unittest.main()
