#! /usr/bin/env python

import os
from unittest import TestCase

import tables
import uuid
import numpy as np
from numpy.testing import assert_array_almost_equal 
from numpy.testing import assert_almost_equal 
from nose.tools import assert_equal, assert_true

from helper import check_cmd, run_cyclus, table_exist, find_ids

class TestRegression(TestCase):
    """A base class for all regression tests. A derived class is required for
    each new input file to be tested. Each derived class *must* declare an `inf`
    member in their `__init__` function that points to the input file to be
    tested, e.g., `self.inf_ = ./path/to/my/input_file.xml. See below for
    examples.
    """
    def __init__(self, *args, **kwargs):
        super(TestRegression, self).__init__(*args, **kwargs)
        self.outf = str(uuid.uuid4()) + ".h5"
        self.inf = None

    def __del__(self):
        if os.path.isfile(self.outf):
            print("removing {0}".format(self.outf))
            os.remove(self.outf)

    def setUp(self):
        if not self.inf:
            raise TypeError(("self.inf must be set in derived classes "
                             "to run regression tests."))
        run_cyclus("cyclus", os.getcwd(), self.inf, self.outf)        

        with tables.open_file(self.outf, mode="r") as f:
            # Get specific tables and columns
            self.agent_entry = f.get_node("/AgentEntry")[:]
            self.agent_exit = f.get_node("/AgentExit")[:] if "/AgentExit" in f \
                else None
            self.resources = f.get_node("/Resources")[:]
            self.transactions = f.get_node("/Transactions")[:]
            self.compositions = f.get_node("/Compositions")[:]
            self.info = f.get_node("/Info")[:]
            self.rsrc_qtys = {
                x["ResourceId"]: x["Quantity"] for x in self.resources}
                        
    def tearDown(self):
        if os.path.isfile(self.outf):
            print("removing {0}".format(self.outf))
            os.remove(self.outf)

class TestPhysorEnrichment(TestRegression):
    """This class tests the 1_Enrichment_2_Reactor.xml file related to the
    Cyclus Physor 2014 publication. The number of key facilities, the enrichment
    values, and the transactions to each reactor are tested.
    """
    def __init__(self, *args, **kwargs):
        super(TestPhysorEnrichment, self).__init__(*args, **kwargs)
        self.inf = "../input/physor/1_Enrichment_2_Reactor.xml"

    def setUp(self):
        super(TestPhysorEnrichment, self).setUp()
        tbl = self.agent_entry
        self.rx_id = find_ids(":cycamore:Reactor", 
                              tbl["Spec"], tbl["AgentId"])
        self.enr_id = find_ids(":cycamore:EnrichmentFacility", 
                               tbl["Spec"], tbl["AgentId"])

        with tables.open_file(self.outf, mode="r") as f:
            self.enrichments = f.get_node("/Enrichments")[:]

    def test_deploy(self):
        assert_equal(len(self.rx_id), 2)
        assert_equal(len(self.enr_id), 1)

    def test_swu(self):
        enr = self.enrichments
        # this can be updated if/when we can call into the cyclus::toolkit's
        # enrichment module from python
        # with old BatchReactor: exp = [6.9, 10, 4.14, 6.9]
        exp = [6.9, 10., 4.14, 6.9]
        obs = [np.sum(enr["SWU"][enr["Time"] == t]) for t in range(4)]
        assert_array_almost_equal(exp, obs, decimal=2)

    def test_nu(self):
        enr = self.enrichments
        # this can be updated if/when we can call into the cyclus::toolkit's
        # enrichment module from python

        # with old BatchReactor: exp = [13.03, 16.54, 7.83, 13.03]
        exp = [13.03, 16.55, 7.82, 13.03]
        obs = [np.sum(enr["Natural_Uranium"][enr["Time"] == t]) \
                   for t in range(4)]
        assert_array_almost_equal(exp, obs, decimal=2)

    def test_xactions(self):
        # reactor 1 transactions
        exp = [1, 1, 1, 1]
        txs = [0, 0, 0, 0]
        for tx in self.transactions:
            if tx['ReceiverId'] == self.rx_id[0]:
                txs[tx['Time']] += self.rsrc_qtys[tx['ResourceId']]

        msg = "Testing that first reactor gets less than it wants."      
        assert_array_almost_equal(exp, txs, decimal=2, err_msg=msg)

        # reactor 2 transactions
        exp = [1, 0.8, 0.2, 1]
        txs = [0, 0, 0, 0]
        for tx in self.transactions:
            if tx['ReceiverId'] == self.rx_id[1]:
                txs[tx['Time']] += self.rsrc_qtys[tx['ResourceId']]

        msg = "Testing that second reactor gets what it wants."      
        assert_array_almost_equal(exp, txs, decimal=2, err_msg=msg)
        
class TestPhysorSources(TestRegression):
    """This class tests the 2_Sources_3_Reactor.xml file related to the Cyclus
    Physor 2014 publication. Reactor deployment and transactions between
    suppliers and reactors are tested.
    """
    def __init__(self, *args, **kwargs):
        super(TestPhysorSources, self).__init__(*args, **kwargs)
        self.inf = "../input/physor/2_Sources_3_Reactors.xml"

    def setUp(self):
        super(TestPhysorSources, self).setUp()
        
        # identify each reactor and supplier by id
        tbl = self.agent_entry
        rx_id = find_ids(":cycamore:Reactor", 
                         tbl["Spec"], tbl["AgentId"])
        self.r1, self.r2, self.r3 = tuple(rx_id)
        s_id = find_ids(":cycamore:Source", 
                        tbl["Spec"], tbl["AgentId"])
        self.smox = self.transactions[0]["SenderId"]
        s_id.remove(self.smox)
        self.suox = s_id[0]

    def test_rxtr_deployment(self):
        depl_time = {x["AgentId"]: x["EnterTime"] for x in self.agent_entry}
        
        assert_equal(depl_time[self.r1], 1)
        assert_equal(depl_time[self.r2], 2)
        assert_equal(depl_time[self.r3], 3)

    def test_rxtr1_xactions(self):
        mox_exp = [0, 1, 1, 1, 0]
        txs = [0, 0, 0, 0, 0]
        for tx in self.transactions:
            if tx['ReceiverId'] == self.r1 and tx['SenderId'] == self.smox:
                txs[tx['Time']] += self.rsrc_qtys[tx['ResourceId']]
        assert_array_almost_equal(mox_exp, txs)
        
        uox_exp = [0, 0, 0, 0, 1]
        txs = [0, 0, 0, 0, 0]
        for tx in self.transactions:
            if tx['ReceiverId'] == self.r1 and tx['SenderId'] == self.suox:
                txs[tx['Time']] += self.rsrc_qtys[tx['ResourceId']]
        assert_array_almost_equal(uox_exp, txs)
         
    def test_rxtr2_xactions(self):
        mox_exp = [0, 0, 1, 1, 1]
        txs = [0, 0, 0, 0, 0]
        for tx in self.transactions:
            if tx['ReceiverId'] == self.r2 and tx['SenderId'] == self.smox:
                txs[tx['Time']] += self.rsrc_qtys[tx['ResourceId']]
        assert_array_almost_equal(mox_exp, txs)
        
        uox_exp = [0, 0, 0, 0, 0]
        txs = [0, 0, 0, 0, 0]
        for tx in self.transactions:
            if tx['ReceiverId'] == self.r2 and tx['SenderId'] == self.suox:
                txs[tx['Time']] += self.rsrc_qtys[tx['ResourceId']]
        assert_array_almost_equal(uox_exp, txs)
         
    def test_rxtr3_xactions(self):
        mox_exp = [0, 0, 0, 0.5, 1]
        txs = [0, 0, 0, 0, 0]
        for tx in self.transactions:
            if tx['ReceiverId'] == self.r3 and tx['SenderId'] == self.smox:
                txs[tx['Time']] += self.rsrc_qtys[tx['ResourceId']]
        assert_array_almost_equal(mox_exp, txs)
        
        uox_exp = [0, 0, 0, 0.5, 0]
        txs = [0, 0, 0, 0, 0]
        for tx in self.transactions:
            if tx['ReceiverId'] == self.r3 and tx['SenderId'] == self.suox:
                txs[tx['Time']] += self.rsrc_qtys[tx['ResourceId']]
        assert_array_almost_equal(uox_exp, txs)

class TestDynamicCapacitated(TestRegression):
    """Tests dynamic capacity restraints involving changes in the number of
    source and sink facilities.

    A source facility is expected to offer a commodity of amount 1,
    and a sink facility is expected to request for a commodity of amount 1.
    Therefore, number of facilities correspond to the amounts of offers
    and requests.

    At time step 1, 3 source facilities and 2 sink facilities are deployed, and
    at time step 2, additional 2 sink facilities are deployed. After time
    step 2, the older 2 sink facilities are decommissioned.
    According to this deployment schedule, at time step 1, only 2 transactions
    are expected, the number of sink facilities being the constraint; whereas,
    at time step 2, only 3 transactions are expected, the number of source
    facilities being the constraint. At time step 3, after decommissioning 2
    older sink facilities, the remaining number of sink facilities becomes
    the constraint, resulting in the same transaction amount as in time step 1.
    """
    def __init__(self, *args, **kwargs):
        super(TestDynamicCapacitated, self).__init__(*args, **kwargs)
        self.inf = "./input/dynamic_capacitated.xml"

    def setUp(self):
        super(TestDynamicCapacitated, self).setUp()

        # Find agent ids of source and sink facilities
        self.agent_ids = self.agent_entry["AgentId"]
        self.agent_impl = self.agent_entry["Spec"]
        self.depl_time = self.agent_entry["EnterTime"]
        self.exit_time = self.agent_exit["ExitTime"]
        self.exit_ids = self.agent_exit["AgentId"]
        self.source_id = find_ids(":agents:Source", self.agent_impl, 
                                  self.agent_ids)
        self.sink_id = find_ids(":agents:Sink", self.agent_impl, self.agent_ids)

        # Check transactions
        self.sender_ids = self.transactions["SenderId"]
        self.receiver_ids = self.transactions["ReceiverId"]
        self.trans_time = self.transactions["Time"]
        self.trans_resource = self.transactions["ResourceId"]

        # Track transacted resources
        self.resource_ids = self.resources["ResourceId"]
        self.quantities = self.resources["Quantity"]

    def test_source_deployment(self):
        # test number of sources
        assert_equal(len(self.source_id), 3)
        # Test that source facilities are all deployed at time step 1
        for s in self.source_id:
            assert_equal(self.depl_time[np.where(self.agent_ids == s)], 1)

    def test_sink_deployment(self):
        # test number of sinks
        assert_equal(len(self.sink_id), 4)
        # Test that first 2 sink facilities are deployed at time step 1
        # and decommissioned at time step 2
        for i in [0, 1]:
            assert_equal(
                self.depl_time[np.where(self.agent_ids == self.sink_id[i])][0], 1)
            assert_equal(
                self.exit_time[np.where(self.exit_ids == self.sink_id[i])][0], 2)
        # Test that second 2 sink facilities are deployed at time step 2
        # and decommissioned at time step 3
        for i in [2, 3]:
            assert_equal(
                self.depl_time[np.where(self.agent_ids == self.sink_id[i])][0], 2)
            assert_equal(
                self.exit_time[np.where(self.exit_ids == self.sink_id[i])][0], 3)

    def test_xaction_general(self):        
        # Check that transactions are between sources and sinks only
        for s in self.sender_ids:
            assert_equal(len(np.where(self.source_id == s)[0]), 1)
        for r in self.receiver_ids:
            assert_equal(len(np.where(self.sink_id == r)[0]), 1)
        # Total expected number of transactions
        assert_equal(len(self.trans_time), 7)
        # Check that at time step 1, there are 2 transactions
        assert_equal(len(np.where(self.trans_time == 1)[0]), 2)
        # Check that at time step 2, there are 3 transactions
        assert_equal(len(np.where(self.trans_time == 2)[0]), 3)
        # Check that at time step 3, there are 2 transactions
        assert_equal(len(np.where(self.trans_time == 3)[0]), 2)

    def test_xaction_specific(self):                
        # Check that at time step 1, there are 2 transactions with total
        # amount of 2
        quantity = 0
        for t in np.where(self.trans_time == 1)[0]:
            quantity += self.quantities[
                np.where(self.resource_ids == self.trans_resource[t])]
        assert_equal(quantity, 2)

        # Check that at time step 2, there are 3 transactions with total
        # amount of 3
        quantity = 0
        for t in np.where(self.trans_time == 2)[0]:
            quantity += self.quantities[
                np.where(self.resource_ids == self.trans_resource[t])]
        assert_equal(quantity, 3)

        # Check that at time step 3, there are 2 transactions with total
        # amount of 2
        quantity = 0
        for t in np.where(self.trans_time == 3)[0]:
            quantity += self.quantities[
                np.where(self.resource_ids == self.trans_resource[t])]
        assert_equal(quantity, 2)

class TestGrowth(TestRegression):
    """Tests GrowthRegion, ManagerInst, and Source over a 4-time step
    simulation.

    A linear growth demand (y = x + 2) is provided to the growth region. Two
    Sources are allowed in the ManagerInst, with capacities of 2 and 1.1,
    respectively. At t=1, a 2-capacity Source is expected to be built, and at
    t=2 and t=3, 1-capacity Sources are expected to be built.
    """
    def __init__(self, *args, **kwargs):
        super(TestGrowth, self).__init__(*args, **kwargs)
        self.inf = "./input/growth.xml"

    def test_deployment(self):
        agent_ids = self.agent_entry["AgentId"]
        proto = self.agent_entry["Prototype"]
        depl_time = self.agent_entry["EnterTime"]
        
        source1_id = find_ids("Source1", proto, agent_ids)
        source2_id = find_ids("Source2", proto, agent_ids)
    
        assert_equal(len(source2_id), 1)
        assert_equal(len(source1_id), 2)

        assert_equal(depl_time[np.where(agent_ids == source2_id[0])], 1)
        assert_equal(depl_time[np.where(agent_ids == source1_id[0])], 2)
        assert_equal(depl_time[np.where(agent_ids == source1_id[1])], 3)

