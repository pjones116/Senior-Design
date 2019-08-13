# Senior-Design

### POP Final Version - ECE 3915W Spring 2019
$$$ Connor Kraft, Phillip Jones, Rachel Zaltz

The following takes images and sensor data at
specified time intervals, then transfers the images
and data log wirelessly.

Please do the following from your Raspberry Pi's
command line, in order for password-less entry
to function properly (x.x.x.x - destination IP):

'user$ ssh-keygen'
'user$ ssh-copy-id -i ~/.ssh/id_rsa.pub x.x.x.x'

Note: this method requires the remote host's password
to be entered once on the command line of the pi, then
saves a keyset for repeated, any-time access by SSH.

You can test password-less auth with the following:
'user$ ssh x.x.x.x'