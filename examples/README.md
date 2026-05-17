# Examples

`basic_test.robot` is a smoke test. It imports `robotframework_vitro.VitroLibrary`
and verifies that the listener has deployed devices by the time Suite Setup runs.

## Run it

~~~bash
vitrorobot \
    --env-config  path/to/env.json \
    --inventory-config path/to/inventory.json \
    examples/basic_test.robot
~~~

Or directly via robot if you prefer:

~~~bash
robot \
    --listener "robotframework_vitro.VitroListener:env_config=path/to/env.json:inventory_config=path/to/inventory.json" \
    examples/basic_test.robot
~~~
