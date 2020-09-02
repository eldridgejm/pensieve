Feature: List the remote repositories

    Scenario: List the repositories on all stores
        Given the home store has repos "foo", "bar", "baz" with metadata
            """
            {
            "foo": {"topics": ["research"], "description": "This is foo."},
            "bar": {"topics": ["teaching", "research"], "description": "This is bar."},
            "baz": {"topics": [], "description": null}
            }
            """
        When the user invokes
            """
            pensieve list
            """
        Then the output is
        # should be in alphabetical order by repository name
        #
            """
            pensieve-test-user/bar :: github
                description: This is the description.
                topics: code, math, science
            pensieve-test-user/baz :: github
                description: This iz baz.
                topics: math, python, science
            pensieve-test-user/foo :: github
            bar :: home
                description: This is bar.
                topics: research, teaching
            baz :: home
            foo :: home
                description: This is foo.
                topics: research

            """
