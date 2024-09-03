from django.test import TestCase
from .tasks import generate_msa_task
from .models import MultipleSequenceAlignment


class GenerateMsaTest(TestCase):
    def setUp(self):
        pass

    def test_task(self):
        task = generate_msa_task("MRGAGAILRPAARGARDLNPRRDISSWLAQWFP", msa_name="generate_msa_test")
        msa = MultipleSequenceAlignment.objects.filter(id=task.id)
        self.assertTrue(msa.exists())