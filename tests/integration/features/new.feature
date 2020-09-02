Feature: Create a new repository

    Scenario: Create a repository with a unique name on home store
        Given the home store has repos "foo", "bar", "baz".
        When the user invokes
            """
            pensieve new home:steve
            """
        Then the output is
            """
            New repository "home:steve" created.

            """
        And the repository "steve" exists on the client.
        And the repository "steve" exists on the home store.
