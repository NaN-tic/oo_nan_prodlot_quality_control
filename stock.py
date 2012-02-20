##############################################################################
#
# Copyright (c) 2012 NaN Projectes de Programari Lliure, S.L.
#                         All Rights Reserved.
#                         http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv, fields
import netsvc

class stock_production_lot_qc_trigger_test(osv.osv):
    '''
    Model that defines the Quality Control Tests which a Production Lot must 
    to pass in certain situations defined by the Trigger Tag.
    '''
    _name = 'stock.production.lot.qc.trigger.test'
    _description = 'Quality Control Test Triggers by Lot'
    _order = 'prodlot_id, sequence'
    
    
    def name_get(self, cr, uid, ids, context=None):
        res = []
        for trigger in self.read(cr, uid, ids, ['trigger_id', 'template_type'], 
                context):
            name = trigger['trigger_id'][1] + ", " + trigger['template_type']
            res.append((trigger['id'], name))
        return res
    
    # stock.production.lot.qc.trigger.test
    def _calc_test_state_data(self, cr, uid, ids, fieldnames, args, 
            context=None):
        """
        Calcs the value of fields 'test_approved' and 'test_success'.
        The 'test_approved' field will be true if its test is in 'success' or 
        'failed' final states, and the fields 'test_success' will be True only 
        if its test is in 'success' state.
        """
        res = {}
        for lot_trigger in self.browse(cr, uid, ids, context):
            res[lot_trigger.id] = {}.fromkeys(fieldnames, False)
            
            if (not lot_trigger.test_id or 
                    lot_trigger.test_id.state not in ('success', 'failed')):
                continue
            
            if 'test_approved' in fieldnames:
                res[lot_trigger.id]['test_approved'] = True
            if ('test_success' in fieldnames and 
                    lot_trigger.test_id.state == 'success'):
                res[lot_trigger.id]['test_success'] = True
        return res
    
    
    _columns = {
        'prodlot_id': fields.many2one('stock.production.lot', 'Lot', 
                required=True),
        'sequence': fields.integer('Sequence', required=True),
        'trigger_id': fields.many2one('qc.trigger', 'Trigger', required=True,
                help="The Quality Control Trigger Tag which defines when must "
                "to be created a Test (using the specified template) for a "
                "Production Lot of this Product."),
        'template_type': fields.selection([
                    ('generic', 'Generic'),
                    ('related', 'Specific'),
                ], "Template's Type", required=True),
        'test_id': fields.many2one('qc.test', 'Test', required=True,
                domain="[('test_template_id.type','=',template_type)]"),
        'test_approved': fields.function(_calc_test_state_data, method=True, 
                type='boolean', string="Test approved?", multi='test_state'),
        'test_success': fields.function(_calc_test_state_data, method=True, 
                type='boolean', string="Test success?", multi='test_state'),
    }
    
    _defaults = {  
        'sequence': 0,
    }
    
    _sql_constraints = [
        ('prodlot_trigger_type_uniq', 
                'unique (prodlot_id, trigger_id, template_type)', 
                "The tuple QC Trigger Tag and Template Type must be unique for "
                "each Production Lot!"),
    ]
stock_production_lot_qc_trigger_test()


class stock_production_lot(osv.osv):
    '''
    Adds to the Lot an 'state' field and a workflow to manage its status related
    to the Quality test that has passed.
    It also adds one2many field to the model which defines the Quality Control 
    Tests that it must to pass.
    '''
    _inherit = 'stock.production.lot'
    
    # stock.production.lot
    def _get_available_states(self, cr, uid, context=None):
        """
        Returns the list of available states for Lot objects. It is defined as 
        a function to make easier to extend the list of states.
        """
        return [
            ('draft', 'Draft'),
            ('pending_test', 'Waiting QC Test'),
            ('valid', 'Valid'),
            ('test_failed', 'QC Test Failed'),
            ('cancel', 'Cancelled'),
        ]
    
    # stock.production.lot
    def get_available_states(self, cr, uid, context=None):
        """
        Returns the list of available states for Lot objects.
        It call's the function '_get_available_states' which could be 
        reimplemented to extend or modify the list of available states.
        @see: _get_available_states
        """
        return self._get_available_states(cr, uid, context)
    
    # stock.production.lot
    def _calc_test_trigger_ro_ids(self, cr, uid, ids, fieldname, args, 
            context=None):
        res = {}
        for lot_triggers in self.read(cr, uid, ids, ['qc_test_trigger_ids'],
                context):
            res[lot_triggers['id']] = lot_triggers['qc_test_trigger_ids']
        return res
    
    
    _columns = {
        # adds the 'readonly' and 'states' attributes
        'product_id': fields.many2one('product.product', 'Product', 
                required=True, readonly=True, 
                states={'draft': [('readonly', False)]}),
        'state': fields.selection(get_available_states, 
                'State', required=True, readonly=True),
#        'state': fields.selection(
#                lambda self, cr, uid, context=None: self.get_available_states, 
#                'State', required=True, readonly=True),
        
        'qc_test_trigger_ids': fields.one2many(
                'stock.production.lot.qc.trigger.test', 'prodlot_id', 
                'QC Tests', help="Defines the Quality Control Tests that this "
                "Production Lot must to pass in certain situations defined by "
                "the Trigger Tag."),
        # Read Only version of previous field. Better solutions are wellcome
        'qc_test_trigger_ro_ids': fields.function(_calc_test_trigger_ro_ids, 
                method=True, type='one2many', string='QC Tests', 
                relation='stock.production.lot.qc.trigger.test'),
        'current_qc_test_trigger_id': fields.many2one(
                'stock.production.lot.qc.trigger.test', 
                'Current QC Test Trigger', 
                domain="[('id','in',[x.id for x in qc_test_trigger_ids])]", readonly=True,
                states={'valid':[('readonly',False)]}),
        'current_qc_test_id': fields.related('current_qc_test_trigger_id', 
                'test_id', type='many2one', relation='qc.test', 
                string="Current QC Test", readonly=True),
    }
    
    _defaults = {  
        'state': 'draft',
    }
    
    # stock.production.lot
    def action_wofkflow_draft(self, cr, uid, ids, context=None):
        """
        Sets the State of Lot to 'Draft'
        """
        self.write(cr, uid, ids, {'state': 'draft'}, context)
        return True
    
    
    # stock.production.lot
    def test_pending_test(self, cr, uid, ids, context=None):
        """
        Checks that Production Lot has a Current Test and it is not Approved 
        (test is not in any final state)
        """
        for prodlot in self.browse(cr, uid, ids, context):
            if (not prodlot.current_qc_test_id or 
                    prodlot.current_qc_test_trigger_id.test_approved):
                return False
        return True
    
    
    # stock.production.lot
    def action_wofkflow_pending_test(self, cr, uid, ids, context=None):
        """
        Sets the State of Lot to 'Pending Test'
        """
        assert len(ids) == 1, "Unexpected number of Lot IDs in function of " \
                "'Pending Test' workflow step."
        
        self.write(cr, uid, ids, {'state': 'pending_test'}, context)
        return self.browse(cr, uid, ids[0], context).current_qc_test_id.id
    
    
    # stock.production.lot
    def test_valid(self, cr, uid, ids, context=None):
        """
        Checks that Production Lot doesn't has Current Test or it is in 
        'Success' state.
        """
        for prodlot in self.browse(cr, uid, ids, context):
            if (prodlot.current_qc_test_id and 
                    prodlot.current_qc_test_id.state!='success'):
                return False
        return True
    
    
    # stock.production.lot
    def action_wofkflow_valid(self, cr, uid, ids, context=None):
        """
        Sets the State of Lot to 'Valid' and, for Lots with Current Test, 
        search the next Test with the same Trigger (ordered by Test Trigger 
        sequence) and, if it exists, sets as 'Current QC Test Trigger' and 
        move the workflow of Lot to 'Next Test' step.
        """
        assert len(ids) == 1, "Unexpected number of Lot IDs in function of " \
                "'Pending Test' workflow step."
        
        trigger_proxy = self.pool.get('stock.production.lot.qc.trigger.test')
        wf_service = netsvc.LocalService("workflow")
        
        prodlot = self.browse(cr, uid, ids[0], context)
        if not prodlot.current_qc_test_id:
            return True
        
        current_trigger = prodlot.current_qc_test_trigger_id
        next_trigger_ids = trigger_proxy.search(cr, uid, [
                    ('prodlot_id', '=', prodlot.id),
                    ('id', '!=', current_trigger.id),
                    ('sequence', '>=', current_trigger.sequence),
                    ('trigger_id', '=', current_trigger.trigger_id.id),
                ], limit=1, context=context)
        
        if next_trigger_ids:
            prodlot_w_next_test.append(prodlot.id)
            self.write(cr, uid, prodlot.id, {
                        'current_qc_test_trigger_id': next_trigger_ids[0],
                        'state': 'valid',
                    }, context)
            
            wf_service.trg_validate(uid, 'stock.production.lot', 
                    next_trigger_ids[0], 'next_test', cr)
            return True
        
        self.write(cr, uid, ids, {'state': 'valid'}, context)
        return current_trigger.test_id.id
    
    
    # stock.production.lot
    def action_wofkflow_test_failed(self, cr, uid, ids, context=None):
        """
        Sets the State of Lot to 'Test Failed' and returns the ID of current 
        Test
        """
        assert len(ids) == 1, "Unexpected number of Lot IDs in function of " \
                "'Pending Test' workflow step."
        
        prodlot = self.browse(cr, uid, ids[0], context)
        self.write(cr, uid, ids, {'state': 'test_failed'}, context)
        return prodlot.current_qc_test_trigger_id.test_id.id
    
    
    # stock.production.lot
    def action_wofkflow_cancel(self, cr, uid, ids, context=None):
        """
        Sets the State of Lot to 'Cancel' and leave empty the 'Current QC Test 
        Trigger' field.
        """
        self.write(cr, uid, ids, {
                    'current_qc_test_trigger_id': False,
                    'state': 'cancel',
                }, context)
        return True
stock_production_lot()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
