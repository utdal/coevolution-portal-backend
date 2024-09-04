from django.test import TestCase
from django.core.files.base import ContentFile
import numpy as np
from .tasks import (
    generate_msa_task,
    compute_dca_task,
    map_residues_task,
    generate_contacts_task,
)
from .models import (
    SeedSequence,
    MultipleSequenceAlignment,
    DirectCouplingAnalysis,
    MappedDi,
    StructureContacts,
)


class GenerateMsaTest(TestCase):
    def setUp(self):
        pass

    def test_task(self):
        task = generate_msa_task.test(
            "MRGAGAILRPAARGARDLNPRRDISSWLAQWFPRTPARSVVALKTPIKVELVAGKTYRWCVCGRSKKQPFCDGSHFFQRTGLSPLKFKAQETRMVALCTCKATQRPPYCDGTHRSERVQKAEVGSPL",
            msa_name="msa_test",
        )
        msa = MultipleSequenceAlignment.objects.filter(id=task.id)
        self.assertTrue(msa.exists())


class ComputeDcaTest(TestCase):
    def setUp(self):
        self.msa = MultipleSequenceAlignment.objects.create(
            fasta=ContentFile(
                "\n".join(
                    [
                        ">sp|P0C7P0|CISD3_HUMAN/1-127 [subseq from] CDGSH iron-sulfur domain-containing protein 3, mitochondrial OS=Homo sapiens OX=9606 GN=CISD3 PE=1 SV=1",
                        "MRGAGAILRPAARGARDLNPRRDISSWLAQWFPRTPARSVVALKTPIKVELVAGKTYRWCVCGRSKKQPFCDGSHFFQRTGLSPLKFKAQETRMVALCTCKATQRPPYCDGTHRSERVQKAEVGSPL",
                        ">sp|B1AR13|CISD3_MOUSE/30-137 [subseq from] CDGSH iron-sulfur domain-containing protein 3, mitochondrial OS=Mus musculus OX=10090 GN=Cisd3 PE=1 SV=1",
                        "-------------------QRREISSWLARWFPKDPAKPVVAQKTPIRLELVAGKTYRWCVCGRSKNQPFCDGSHFFQRTGLSPLKFKAQETRTVALCTCKATQRPPYCDGTHKSEQVQKAEVGSPL",
                        ">sp|B0K020|CISD1_RAT/67-108 [subseq from] CDGSH iron-sulfur domain-containing protein 1 OS=Rattus norvegicus OX=10116 GN=Cisd1 PE=3 SV=1",
                        "------------------------------------------------------DKAVYCRCWRSKKFPFCDGAHIKHETGVGPLIIKKKET-----------------------------------",
                        ">sp|Q91WS0|CISD1_MOUSE/68-108 [subseq from] CDGSH iron-sulfur domain-containing protein 1 OS=Mus musculus OX=10090 GN=Cisd1 PE=1 SV=1",
                        "-------------------------------------------------------KAVYCRCWRSKKFPFCDGAHIKHETGVGPLIIKKKET-----------------------------------",
                        ">sp|Q9NZ45|CISD1_HUMAN/67-107 [subseq from] CDGSH iron-sulfur domain-containing protein 1 OS=Homo sapiens OX=9606 GN=CISD1 PE=1 SV=1",
                        "------------------------------------------------------DKAVYCRCWRSKKFPFCDGAHTKHETGVGPLIIKKKE------------------------------------",
                        ">sp|B3RML8|CISD2_TRIAD/97-120 [subseq from] CDGSH iron-sulfur domain-containing protein 2 homolog OS=Trichoplax adhaerens OX=10228 GN=TRIADDRAFT_21706 PE=3 SV=1",
                        "---------------------------------------------------V-GEKLVFCRCWRSKKFPYCDGSHN---------------------------------------------------",
                    ]
                ),
                "dca_test",
            )
        )

    def test_task(self):
        task = compute_dca_task.test(self.msa.id)
        dca = DirectCouplingAnalysis.objects.filter(id=task.id)
        self.assertTrue(dca.exists())
        self.assertEqual(dca.first().ranked_di.shape, (127 * 126 // 2, 3))


class MapResiduesTest(TestCase):
    def setUp(self):
        self.seed = SeedSequence.objects.create(
            fasta=ContentFile(
                ">sp|P0C7P0|CISD3_HUMAN CDGSH iron-sulfur domain-containing protein 3, mitochondrial OS=Homo sapiens OX=9606 GN=CISD3 PE=1 SV=1\n"
                "MRGAGAILRPAARGARDLNPRRDISSWLAQWFPRTPARSVVALKTPIKVELVAGKTYRWCVCGRSKKQPFCDGSHFFQRTGLSPLKFKAQETRMVALCTCKATQRPPYCDGTHRSERVQKAEVGSPL",
                "map_residues_test",
            )
        )

        self.dca = DirectCouplingAnalysis.objects.create(
            ranked_di=np.array([[1, 8, 3.0], [5, 15, 8.0]])
        )

    def test_task(self):
        task = map_residues_task.test(self.dca.id, "6AVJ", self.seed.id, "A", "A")
        mappedDi = MappedDi.objects.filter(id=task.id)
        self.assertTrue(mappedDi.exists())
        self.assertTrue(
            np.allclose(
                mappedDi.first().mapped_di.tolist(),
                [(40, 50, 8.0), (36, 43, 3.0)],
            )
        )


class GenerateContactsTest(TestCase):
    def setUp(self):
        pass

    def test_task(self):
        task = generate_contacts_task.test(
            "6AVJ"
        )
        mappedDi = StructureContacts.objects.filter(id=task.id)
        self.assertTrue(mappedDi.exists())
