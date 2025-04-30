import constants as c

class CommandBuilder:
    def __init__(self, logger, args):
        self.logger = logger
        self.args = args
        self.ok = False

    def _get_command_options(self, command_dict):
        """Get additional options for the command"""
        input_options = self.args.task_options
        param_string = ""

        # set true - set false if we have issues here
        self.ok = True

        for param, props in command_dict["option_list"].items():
            param_type = props["type"]
            param_required = props["required"]

            # Was the param passed as an input
            input_param = input_options.get(param, None) if input_options else None

            if input_param is None:
                ask_for = input("Enter value for %s: " % param)
                if (ask_for is None or len(ask_for) == 0) and param_required:
                    self.logger.error("Parameter %s is required, unable to continue")
                    self.ok = False
                    return None
                else:
                    param_string += " %s %s" % (param, ask_for)
            else:
                param_string += " %s %s" % (param, input_param)

        if len(param_string) > 0:
            return param_string
        
        return None


    def get_command(self):
        """Figure out the command to use based on the choice made"""
        task_dict = c.CHOICES_TASKS.get(self.args.task, None)
        self.ok = False

        if task_dict is None:
            c.logger.error("Invalid task selected")
            return None
        
        # Example - task is "services", option is "list" or "restart"
        command_dict = task_dict.get(self.args.option, None)

        if command_dict is None:
            _msg = "\n"
            for k in task_dict:
                _msg += "  %s\n" % k

            self.logger.error("Invalid task option - the valid options are: %s", _msg)
            return None
        
        if command_dict["has_options"]:
            param_string = self._get_command_options(command_dict)

            if param_string is not None and len(param_string) > 0:
                command_dict["command"] += param_string
        else:
            self.ok = True

        return command_dict        