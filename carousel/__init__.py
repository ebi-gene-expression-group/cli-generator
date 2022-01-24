from option_writer import ROption


class RCarousel:

    def __init__(self, command):
        self._selection_option = { 'type': 'string',
                                   'long': command['long'],
                                   'default': command['default'] }
        if command['help']:
            self._selection_option['help'] = command['help']
        self._command = command
        self.options = self._compute_options()
        self.sub_commands = self._compute_subcommands()
        self.dependencies = self._compute_dependencies()

    def get_commands(self):
        return self.sub_commands

    def get_options(self):
        return self.options

    def _compute_dependencies(self):
        dependencies = set()
        for call in self._command['selector']:
            dependencies.update(call['dependencies'])

        return list(dependencies)

    def _compute_options(self):
        options = [self._selection_option]
        for call in self._command['selector']:
            options.extend(call['options'])
        return options

    def _compute_subcommands(self):
        """
        Adds all subcommands plus conditionality to just execute one of them:

        if (opt$<carousel_log> == '<carousel_option_1>' ) {
            <carousel_1_call>
        } else if (opt$<carousel_log> == '<carousel_option_1>' ) {
            <carousel_2_call>
        } ... {
            <carousel_n_call>
        }

        by using rcode blocks between command calls, so that the above is the result of the command writer.
        :return:
        """
        commands = []
        if_prefix = ""
        selector_option = ROption.create_option(self._selection_option)
        for command in self._command['selector']:
            selector = {'call': f"selector_{command['call']}",
                        'rcode': f"{if_prefix}if ( opt${selector_option.long_value()} == '{command['call']}' ) {{ "
                       }
            if_prefix = "} else "
            commands.append(selector)
            commands.append(command)

        closing = {'call': f"selector_closing",
                   'rcode': "}"
                   }
        commands.append(closing)
        return commands