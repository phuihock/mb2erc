from generators import PaymentFile
from unittest import TestCase

class PaymentFileTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_generate_empty_payment_file(self):
        pf = PaymentFile()
        pf.set_header()
        pf.set_footer()

        header, footer = pf.out()
        self.assertEquals(header[:2], '00')
        self.assertEquals(footer[:2], '99')