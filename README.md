# MCFE Galaxy

## Triggering events

Randall includes services which listen for events on a MQTT broker. 
These events cause further events to be triggered which may include:
- updating the metadata in Fuseki
- running workflows on Galaxy

To see an example of this in action you can run the following command:

```bash
mosquitto_pub -u {{YOUR_USER}} -P {{YOUR_PASS}} -t '/parameter/update/01234' -m '{"MajorRadius": "8.5"}
```

If you want to see the logs of the Crater service, you can do so by running:

```bash
mosquitto_sub -u {{YOUR_USER}} -P {{YOUR_PASS}} -t '/#' -v
```

## Useful web interfaces

Randall is made of serveral tools which provide web interfaces. These include:
- Fuseki: http://fuseki.localhost (default username: `admin`, default password: `admin`)
  * This is a triplestore which stores the metadata
- Galaxy: http://galaxy.localhost (username and password from .env file)
  * This is a workflow manager which runs workflows
- Traefik: http://localhost:8888 (no authentication)
  * This is a reverse proxy which routes traffic to the appropriate service
