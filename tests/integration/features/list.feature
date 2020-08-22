Feature: List the remote repositories

    Scenario: List the repositories on all stores
        Given the home store has repos "foo", "bar", "baz" with metadata
            """
            {
            "foo": {"tags": ["research"], "description": "This is foo."},
            "bar": {"tags": ["teaching", "research"], "description": "This is bar."},
            "baz": {"tags": [], "description": 2}
            }
            """
        When the user invokes
            """
            pensieve list
            """
        Then the output is
        # should be in alphabetical order by repository name
            """
            bar :: home
                description: This is bar.
                tags: {research, teaching}
            baz :: home
                description: None
                tags: None
            foo :: home
                description: This is foo.
                tags: {research}    
            """
