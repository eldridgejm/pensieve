This creates a Docker image of a server which has the pensieve-agent script
installed.

To use it, `docker build` the image, then `docker run -d -P` the image. Then
find the port with a `docker ps`, and `ssh` into it with `ssh tester@0.0.0.0 -p
<port>`. The password is `testing`.

The id_rsa in this directory is an identity key that grants passwordless access
to the container. It is recommended that you use something like this to squelch
the prompt about accessing an unknown system:

    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null tester@0.0.0.0 -p <port> -i id_rsa

And if you're reading this thinking that you've discovered an unprotected private key
to my personal server full of my financial information, sorry... but this ain't it.
