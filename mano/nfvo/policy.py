from threading import Timer
import pdb

class PeriodicTimer(object):
    """ Sends periodic stats requests
        through the callback function parameter """
    def __init__(self, interval, maxticks, callback, *args, **kwargs):
        """
            @param interval : interval
            @param maxticks : nbr of execution
            @param callback : dynamic function which is executed
        """
        self._interval = interval
        self._callback = callback
        self._args = args
        self._kwargs = kwargs
        if maxticks:
            self._nticks = 0
            self._maxticks = maxticks
        else:
            self._maxticks = None

    def _run(self):
        """ function executed by threads """
        if self._maxticks:
            self._nticks += 1
            if self._nticks < self._maxticks:
                self._timer = Timer(self._interval, self._run)
                self._timer.start()
        else:
            self._timer = Timer(self._interval, self._run)
            self._timer.start()
        # sends the request
        self._callback(*self._args, **self._kwargs)

    def start(self):
        """ launches threads """
        self._timer = Timer(self._interval, self._run)
        self._timer.start()

    def stop(self):
        """ stops threads"""
        self._timer.cancel()

class Policy(object):
    """
    base classe for policies
    """
    def __init__(self, policy_type, target_list):

        self._type = policy_type
        self._targets = target_list
        self._triggers = None

    @property
    def type(self):
        return self._type

    @property
    def targets(self):
        return self._targets

    @property
    def triggers(self):
        return self._triggers


class Trigger(object):

    def __init__(self, event, condition, action):

        self._event = event
        self._condition = condition
        self._action = action

    @property
    def event(self):
        return self._event

    @property
    def condition(self):
        return self._condition

    @property
    def action(self):
        return self._action


class SignatureVerPolicy(Policy):
    """

    """
    def __init__(self, policy_type, target_list, triggers_list):

        Policy.__init__(self, policy_type, target_list)
        self._triggers = self.create_triggers(triggers_list)

    def create_triggers(self, triggers_list):

        triggers = []
        for trigger in triggers_list:
            event = trigger.get_event()
            action = trigger.get_action()
            condition = trigger.get_condition()['constraint']
            key_word, constraint = condition.split(' ')
            try:
                assert key_word == "triggred_by"
            except AssertionError:
                print "constraint assertion error"
            triggers.append(Trigger(event, constraint, action))
        return triggers

    def evaluate(self, vnf):
        actions = []
        for trigger in self.triggers:
            if trigger.condition == vnf:
                actions.append(trigger.action)
        return actions


class UpdateFirewallPolicy(Policy):
    """

    """
    def __init__(self, policy_type, target_list, triggers_list):

        Policy.__init__(self, policy_type, target_list)
        self._triggers = self.create_triggers(triggers_list)

    def create_triggers(self, triggers_list):

        triggers = []
        for trigger in triggers_list:
            event = trigger.get_event()
            action = trigger.get_action()
            condition = trigger.get_condition()['constraint']
            key_word, constraint = condition.split(' ')
            try:
                assert key_word == "triggred_by"
            except AssertionError:
                print "constraint assertion error"
            triggers.append(Trigger(event, constraint, action))
        return triggers

    def evaluate(self, vnf):
        for trigger in self.triggers:
            if trigger.condition == vnf:
                return trigger.action
        return None




class PeriodicTrigger(object):

    def __init__(self, target, meter_name, callback, event, condition, action):

        self._target = target
        self._callback = callback
        self._meter_name = meter_name
        self._data = None
        self._event = event
        self._condition = condition
        self._action = action
        self._timer = self.init_periodic_timer(condition)
        self._timer.start()

    @property
    def target(self):
        return self._target

    @property
    def event(self):
        return self._event

    @property
    def condition(self):
        return self._condition

    @property
    def action(self):
        return self._action

    @property
    def data(self):
        return self._data

    @property
    def meter_name(self):
        return self._meter_name

    def set_meter_value(self, value):
        self._data = value

    def init_periodic_timer(self, condition):
        period = condition['period']
        return PeriodicTimer(period, None, self.evaluate)

    def evaluate(self):
        print 'Evaluating policy condition for targets: {0}'.format(self.target)
        if self.condition['comparison_operator'] == 'gt':
            if self.data > self.condition['threshold']:
                #print '{0} greater_than {1} : condition satisfied'.format(self.data, self.condition['threshold'])
                self.trigger()
            else:
		pass
                #print '{0} lesser_than {1} : condition NOT satisfied'.format(self.data, self.condition['threshold'])
        elif self.condition['comparison_operator'] == 'lt':
            if self.data < self.condition['threshold']:
                #print '{0} lesser_than {1} : condition satisfied'.format(self.data, self.condition['threshold'])
                self.trigger()
            else:
		pass
                #print '{0} greater_than {1} : condition NOT satisfied'.format(self.data, self.condition['threshold'])

    def trigger(self):
	self._timer.stop()
        self._callback(self.target, self.action['number'])



class ScalingPolicy(Policy):
    """

    """
    def __init__(self, callback, policy_type, target_list, triggers_list):

        Policy.__init__(self, policy_type, target_list)
        self._callback = callback
        self._triggers = self.create_triggers(triggers_list)

    def create_triggers(self, triggers_list):
        triggers = []
        for target in self.targets:
            for trigger in triggers_list:
                meter_name = trigger.trigger_tpl['meter_name']
                event = trigger.get_event()
                action = trigger.get_action()
                condition = trigger.get_condition()
                triggers.append(PeriodicTrigger(target,
                                                meter_name,
                                                self._callback,
                                                event,
                                                condition,
                                                action))
        return triggers

    def meter_in(self, meter_name, target, value):
        for trigger in self.triggers:
            if trigger.target == target:
                if trigger.meter_name == meter_name:
                    trigger.set_meter_value(value)
