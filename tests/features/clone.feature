Feature: Clone a repository

    Scenario: Clone a repository from the home store with an existing name
        Given the home store has repos "foo", "bar", "baz".
        When the user invokes
            """
            pensieve clone home foo
            """
        Then the output is
            """
            Cloned repository "foo".

            """
        And the repository "foo" exists on the client.

    Scenario: Clone a repository from the home store which does not exist
        Given the home store has repos "foo", "bar", "baz".
        When the user invokes
            """
            pensieve clone home steve
            """
        Then the output is
            """
            Could not clone the repository "steve" from the server.

            """
