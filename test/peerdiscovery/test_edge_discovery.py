from ipv8.peerdiscovery.discovery import EdgeWalk
from ipv8.deprecated.community import _DEFAULT_ADDRESSES
from test.base import TestBase
from test.mocking.community import MockCommunity
from test.util import twisted_wrapper


class TestEdgeWalk(TestBase):

    def setUp(self):
        while _DEFAULT_ADDRESSES:
            _DEFAULT_ADDRESSES.pop()

        node_count = 3
        self.overlays = [MockCommunity() for _ in range(node_count)]
        self.strategies = [EdgeWalk(self.overlays[i], neighborhood_size=1) for i in range(node_count)]

    def tearDown(self):
        for overlay in self.overlays:
            overlay.unload()

    @twisted_wrapper
    def test_take_step(self):
        """
        Check if we will walk to a random other node.

        Unit test network layout:
          NODE0 <-> NODE1 <-> NODE2
        """
        self.overlays[0].network.add_verified_peer(self.overlays[1].my_peer)
        self.overlays[0].network.discover_services(self.overlays[1].my_peer, [self.overlays[1].master_peer.mid, ])
        self.overlays[1].network.add_verified_peer(self.overlays[2].my_peer)
        self.overlays[1].network.discover_services(self.overlays[2].my_peer, [self.overlays[2].master_peer.mid, ])
        # We expect NODE1 to introduce NODE0 to NODE2
        self.strategies[0].take_step()

        yield self.deliver_messages()

        self.assertEqual(len(self.overlays[0].network.verified_peers), 2)

    @twisted_wrapper
    def test_take_step_into(self):
        """
        Check if we will walk to an introduced node.
        """
        self.strategies[0].edge_timeout = 0.0  # Finish the edge immediately
        self.overlays[0].network.add_verified_peer(self.overlays[1].my_peer)
        self.overlays[0].network.discover_services(self.overlays[1].my_peer, [self.overlays[1].master_peer.mid, ])

        # We expect NODE0 will add NODE1 to its neighborhood and start constructing an edge from it.
        # Don't allow that right now.
        self.strategies[0].take_step()

        yield self.deliver_messages()

        # Now we give NODE2 to NODE1, which it can forward to NODE0 to make an edge
        self.overlays[1].network.add_verified_peer(self.overlays[2].my_peer)
        self.overlays[1].network.discover_services(self.overlays[2].my_peer, [self.overlays[2].master_peer.mid, ])

        # In order:
        # 1. Add root (NODE1) and query for nodes
        # 2. Detect intro (NODE2) from root and query for nodes
        # 3. Detect no more intros from NODE2 and finish edge
        for _ in range(3):
            self.strategies[0].take_step()
            yield self.deliver_messages()

        self.assertEqual(len(self.overlays[0].network.verified_peers), 2)
        self.assertEqual(len(self.strategies[0].complete_edges), 1)

    @twisted_wrapper
    def test_fail_step_into(self):
        """
        Check if we drop an unreachable introduced node.
        """
        self.strategies[0].edge_timeout = 0.0  # Finish the edge immediately
        self.overlays[0].network.add_verified_peer(self.overlays[1].my_peer)
        self.overlays[2].endpoint.close()

        # We expect NODE0 will add NODE1 to its neighborhood and start constructing an edge from it.
        # Don't allow that right now.
        self.strategies[0].take_step()

        yield self.deliver_messages()

        # Now we give NODE2 to NODE1, which it can forward to NODE0 to make an edge
        self.overlays[1].network.add_verified_peer(self.overlays[2].my_peer)
        self.overlays[1].network.discover_services(self.overlays[2].my_peer, [self.overlays[2].master_peer.mid, ])

        # In order:
        # 1. Add root (NODE1) and query for nodes
        # 2. Detect intro (NODE2) from root and query for nodes
        # 3. Fail to walk to NODE2 -> edge is only root, so no complete edge
        for _ in range(3):
            self.strategies[0].take_step()
            yield self.deliver_messages()

        self.assertEqual(len(self.overlays[0].network.verified_peers), 1)
        self.assertEqual(len(self.strategies[0].complete_edges), 0)

    @twisted_wrapper
    def test_complete_edge(self):
        """
        Check if we can complete an edge.
        """
        self.strategies[0].edge_length = 2 # Finish with one other node
        self.strategies[0].edge_timeout = 0.0  # Finish the edge immediately
        self.overlays[0].network.add_verified_peer(self.overlays[1].my_peer)
        self.overlays[0].network.discover_services(self.overlays[1].my_peer, [self.overlays[1].master_peer.mid, ])

        # We expect NODE0 will add NODE1 to its neighborhood and start constructing an edge from it.
        # Don't allow that right now.
        self.strategies[0].take_step()

        yield self.deliver_messages()

        # Now we give NODE2 to NODE1, which it can forward to NODE0 to make an edge
        self.overlays[1].network.add_verified_peer(self.overlays[2].my_peer)
        self.overlays[1].network.discover_services(self.overlays[2].my_peer, [self.overlays[2].master_peer.mid, ])

        # In order:
        # 1. Add root (NODE1) and query for nodes
        # 2. Detect intro (NODE2) from root and query for nodes
        # 3. Detect no more intros from NODE2 and finish edge
        for _ in range(3):
            self.strategies[0].take_step()
            yield self.deliver_messages()

        self.assertEqual(len(self.overlays[0].network.verified_peers), 2)
        self.assertEqual(len(self.strategies[0].complete_edges), 1)
