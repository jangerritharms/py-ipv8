from ipv8.attestation.identity.community import IdentityCommunity
from ipv8.peer import Peer

from test.base import MockIPv8, TestBase
from test.util import twisted_wrapper


class TestIdentityCommunity(TestBase):

    def setUp(self):
        super(TestIdentityCommunity, self).setUp()
        self.initialize(IdentityCommunity, 2)

    def create_node(self):
        return MockIPv8(u"curve25519", IdentityCommunity, working_directory=u":memory:")

    @twisted_wrapper
    def test_advertise(self):
        """
        Check if a node can construct an advertisement for his attestest attribute.
        """
        pk_1 = self.nodes[1].my_peer.public_key.key_to_bin()
        public_peer_1 = Peer(pk_1, self.nodes[1].endpoint.wan_address)

        yield self.introduce_nodes()

        self.nodes[1].overlay.add_known_hash("a"*20, "attribute", self.nodes[0].my_peer.public_key.key_to_bin())
        self.nodes[0].overlay.request_attestation_advertisement(public_peer_1, "a"*20, "attribute")

        yield self.deliver_messages()

        for node_nr in [0, 1]:
            self.assertIsNotNone(self.nodes[node_nr].overlay.persistence.get(pk_1, 1))
            self.assertEqual(self.nodes[node_nr].overlay.persistence.get(pk_1, 1).link_sequence_number, 1)

    @twisted_wrapper
    def test_advertise_reject_hash(self):
        """
        Check if unknown hashes are not signed.
        """
        pk_1 = self.nodes[1].my_peer.public_key.key_to_bin()
        public_peer_1 = Peer(pk_1, self.nodes[1].endpoint.wan_address)

        yield self.introduce_nodes()

        self.nodes[0].overlay.request_attestation_advertisement(public_peer_1, "a" * 20, "attribute")

        yield self.deliver_messages()

        for node_nr in [0, 1]:
            self.assertIsNone(self.nodes[node_nr].overlay.persistence.get(pk_1, 1))

    @twisted_wrapper
    def test_advertise_reject_public_key(self):
        """
        Check if we don't sign correct hashes for the wrong peer.
        """
        pk_1 = self.nodes[1].my_peer.public_key.key_to_bin()
        public_peer_1 = Peer(pk_1, self.nodes[1].endpoint.wan_address)

        yield self.introduce_nodes()

        self.nodes[1].overlay.add_known_hash("a" * 20, "attribute", self.nodes[1].my_peer.public_key.key_to_bin())
        self.nodes[0].overlay.request_attestation_advertisement(public_peer_1, "a" * 20, "attribute")

        yield self.deliver_messages()

        for node_nr in [0, 1]:
            self.assertIsNone(self.nodes[node_nr].overlay.persistence.get(pk_1, 1))

    @twisted_wrapper
    def test_advertise_reject_old(self):
        """
        Check if we don't sign old attestations.
        """
        pk_1 = self.nodes[1].my_peer.public_key.key_to_bin()
        public_peer_1 = Peer(pk_1, self.nodes[1].endpoint.wan_address)

        yield self.introduce_nodes()

        self.nodes[1].overlay.known_attestation_hashes["a" * 20] = ("attribute",
                                                                    0, self.nodes[0].my_peer.public_key.key_to_bin())
        self.nodes[0].overlay.request_attestation_advertisement(public_peer_1, "a" * 20, "attribute")

        yield self.deliver_messages()

        for node_nr in [0, 1]:
            self.assertIsNone(self.nodes[node_nr].overlay.persistence.get(pk_1, 1))

    @twisted_wrapper
    def test_advertise_reject_wrong_name(self):
        """
        Check if we don't sign attestations with incorrect metadata.
        """
        pk_1 = self.nodes[1].my_peer.public_key.key_to_bin()
        public_peer_1 = Peer(pk_1, self.nodes[1].endpoint.wan_address)

        yield self.introduce_nodes()

        self.nodes[1].overlay.add_known_hash("a" * 20, "attribute", self.nodes[1].my_peer.public_key.key_to_bin())
        self.nodes[0].overlay.request_attestation_advertisement(public_peer_1, "a" * 20, "attribute")

        yield self.deliver_messages()

        for node_nr in [0, 1]:
            self.assertIsNone(self.nodes[node_nr].overlay.persistence.get(pk_1, 1))
