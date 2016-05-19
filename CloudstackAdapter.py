import cloudstack
import logging
from cloud_adapters.cloudstack_adapter.cloudstack import Client


logger = logging.getLogger(__name__)


class CloudstackAdapter(object):

  ARG_TRANSLATIONS = {
    # Universal tag:  Cloudstack tag
    'domain_id': 'domainid',
    'start_date': 'startdate',
    'end_date': 'enddate',
    'account_id': 'accountid',
    'zone_id': 'zoneid',
    'account_name': 'name',
    'network_type': 'guestiptype',
    'network_id': 'networkids',
    'job_id': 'jobid',
    'service_offering_id': 'serviceofferingid',
    'template_id': 'templateid',
    'ip_id': 'ipaddressid',
    'vm_id': 'virtualmachineid',
  }

  TAG_VM_ID = 'name'
  TAG_IP_ADDRESS = 'description'
  TAG_VOLUME = ''

  BASE_NETWORK_OFFERING = 'DefaultIsolatedNetworkOfferingWithSourceNatService'

  CLOUDSTACK_USAGE_TYPES = {
    '1': {
      'name': 'Running VM',
      'type': 'RUNNING_VM',
      'is_billed': True,
      'is_singleton': False,
      'is_flatrate': False,
      'has_offering': True,
      'id_tag': TAG_VM_ID
    },
    '2': {
      'name': 'Allocated VM',
      'type': 'ALLOCATED_VM',
      'is_billed': False
    },
    '3': {
      'name': 'IP Address',
      'type': 'IP_ADDRESS',
      'is_billed': True,
      'is_singleton': False,
      'is_flatrate': True,
      'has_offering': False,
      'id_tag': TAG_IP_ADDRESS
    },
    '4': {
      'name': 'Network bytes (tx)',
      'type': 'NETWORK_BYTES_SENT',
      'is_billed': True,
      'is_singleton': True,
      'is_flatrate': False,
      'rate_divisor': 1073741824,  # B -> GB
    },
    '5': {
      'name': 'Network bytes (rx)',
      'type': 'NETWORK_BYTES_RECEIVED',
      'is_billed': True,
      'is_singleton': True,
      'is_flatrate': False,
      'rate_divisor': 1073741824,  # B -> GB
    },
    '6': {
      'name': 'Volume',
      'type': 'VOLUME',
      'is_billed': True,
      'is_singleton': False,
      'is_flatrate': False,
      'has_offering': False,
      'id_tag': TAG_VOLUME,
      'rate_divisor': 1073741824,  # B -> GB
    },
    '7': {
      'name': 'Template',
      'type': 'TEMPLATE',
      'is_billed': True,
      'is_singleton': False,
      'is_flatrate': False,
      'has_offering': False,
      'rate_divisor': 1073741824,  # B -> GB
    },
    '8': {
      'name': 'ISO',
      'type': 'ISO',
      'is_billed': True,
      'is_singleton': False,
      'is_flatrate': False,
      'has_offering': False,
      'rate_divisor': 1073741824,  # B -> GB
    },
    '9': {
      'name': 'Snapshot',
      'type': 'SNAPSHOT',
      'is_billed': True,
      'is_singleton': False,
      'is_flatrate': False,
      'has_offering': False,
      'rate_divisor': 1073741824,  # B -> GB
    },
    '11': {
      'name': 'Load balancer policy',
      'type': 'LOAD_BALANCER_POLICY',
      'is_billed': False,
      'is_singleton': True,
      'is_flatrate': False,
      'has_offering': False,
    },
    '12': {
      'name': 'Port forwarding rule',
      'type': 'PORT_FORWARDING_RULE',
      'is_billed': True,
      'is_singleton': True,
      'is_flatrate': False,
      'has_offering': False,
    },
    '14': {
      'name': 'VPN users',
      'type': 'VPN_USERS',
      'is_billed': False,
      'is_singleton': True,
      'is_flatrate': False,
      'has_offering': False,
    }
  }

  def __init__(self, api, key, secret):
    """
    __init__:  basic contructor function

    api:  Cloudstack API link
    key:  Cloudstack key
    secret:  Cloudstack secret key

    """
    self.adapter = Client(api, key, secret)


  def translate_args(self, args):
    """
    translate_args - translate the universal arguments to Cloudstack-style
          arguments.  This should be run everytime args are passed in.

    """
    for universal_arg, cloudstack_arg in self.ARG_TRANSLATIONS.iteritems():
      if universal_arg in args:
        args[cloudstack_arg] = args[universal_arg]
    return args


  """
  All other functions:
  
    - These functions should take in the ApiAdapter function names, convert to
      this API's function name, and pass the call

    - Should the return data be in a different format than the ApiAdapter is
      expecting, this would be where you would want to do the reformatting as well

  """
  def get_zone_list(self, args={}):
    return self.adapter.listZones(args)


  def get_network_list(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.listNetworks(args)


  def list_network_offerings(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.listNetworkOfferings(args)

  def create_network(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.createNetwork(args)


  def get_host_list(self, args={}):
    return self.adapter.listHosts(args)


  def get_host_capacity(self, args={}):
    return self.adapter.listCapacity(args)


  def get_account_list(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.listAccounts(args)


  def create_account(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.createAccount(args)


  def get_project_list(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.listProjects(args)


  def get_project_accounts(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.listProjectAccounts(args)


  def get_events(self, args={}):
    return self.adapter.listEvents(args)


  def get_event_types(self, args={}):
    return self.adapter.listEventTypes(args)


  def get_alerts(self, args={}):
    return self.adapter.listAlerts(args)


  def get_system_vm_list(self, args={}):
    return self.adapter.listSystemVms(args)


  def get_vm_list(self, args={}):
    return self.adapter.listVirtualMachines(args)


  def get_router_list(self, args={}):
    return self.adapter.listRouters(args)


  def get_job_list(self, args={}):
    return self.adapter.listAsyncJobs(args)

  def get_job_status(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.queryAsyncJobResult(args)


  def associate_ip_address(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.associateIpAddress(args)


  def get_ip_list(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.listPublicIpAddresses(args)


  def get_ipforwarding_rules(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.listPortForwardingRules(args)


  def create_port_forward(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.createPortForwardingRule(args)


  def reboot_router(self, args={}):
    return self.adapter.rebootRouter(args)  


  def start_router(self, args={}):
    return self.adapter.startRouter(args)  


  def stop_router(self, args={}):
    return self.adapter.stopRouter(args)  


  def destroy_router(self, args={}):
    return self.adapter.destroyRouter(args)  


  def restart_network(self, args={}):
    return self.adapter.restartNetwork(args)


  def start_vm(self, args={}):
    return self.adapter.startVirtualMachine(args)


  def stop_vm(self, args={}):
    return self.adapter.stopVirtualMachine(args)


  def restart_vm(self, args={}):
    return self.adapter.rebootVirtualMachine(args)


  def destroy_vm(self, args={}):
    return self.adapter.destroyVirtualMachine(args)


  def get_server_levels(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.listServiceOfferings(args)


  def get_template_list(self, args={}):
    if args: args = self.translate_args(args)
    if 'templatefilter' not in args:
      args['templatefilter'] = 'featured'
    return self.adapter.listTemplates(args)


  def get_disk_offering_list(self, args={}):
    return self.adapter.listDiskOfferings(args)


  def get_usage(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.listUsageRecords(args)


  def launch_vm(self, args={}):
    if args: args = self.translate_args(args)
    return self.adapter.deployVirtualMachine(args)

    