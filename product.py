##############################################################################
#
# Copyright (c) 2010-2012 NaN Projectes de Programari Lliure, S.L.
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

class product_qc_trigger_template(osv.osv):
    '''
    Model to configure Quality Control Templates/Tests triggers by Product.
    Define the template to use for a trigger, ordering it by sequence.
    '''
    _name = 'product.qc.trigger.template'
    _description = 'Quality Control Template Triggers by Product'
    _order = 'product_id, company_id, sequence'
    
    _columns = {
        'product_id': fields.many2one('product.product', 'Product', 
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
        'template_id': fields.many2one('qc.test.template', 'Template', 
                domain="[('type','=',template_type)]", required=True,
                help="The Quality Control Template to use."),
        'company_id': fields.many2one('res.company', 'Company'),
    }
    
    _defaults = {  
        'sequence': 0,
    }
    
    _sql_constraints = [
        ('product_trigger_type_company_uniq', 
                'unique (product_id, trigger_id, template_type, company_id)', 
                "The tuple QC Trigger Tag and Template Type must be unique for "
                "each Product and Company!"),
    ]
product_qc_trigger_template()


class product_product(osv.osv):
    '''
    Adds to the Product a one2many field to the model which configures Quality
    Control Templates/Tests triggers.
    The generic Templates get it's default value from the user's Company.
    '''
    _inherit = 'product.product'
    
    _columns = {
        'qc_template_trigger_ids': fields.one2many(
                'product.qc.trigger.template', 'product_id', 'QC Triggers',
                help="Defines when a Production Lot must to pass a Quality "
                "Control Test (based on the defined Template).\n"
                "It gets its default value for generic templates from the "
                "Company."),
    }
    
    # product.product
    def _default_qc_template_trigger_ids(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        
        res = []
        for generic_trigger in user.company_id.qc_template_trigger_ids:
            res.append({
                        'sequence': generic_trigger.sequence,
                        'trigger_id': generic_trigger.trigger_id.id,
                        'template_type': 'generic',
                        'template_id': generic_trigger.template_id.id,
                        'company_id': user.company_id.id,
                    })
        return res
    
    _defaults = {  
        'qc_template_trigger_ids': _default_qc_template_trigger_ids,
    }
product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
