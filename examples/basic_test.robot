*** Settings ***
Documentation     Smoke example. Run with:
...               vitrorobot --env-config path/to/env.json
...                         --inventory-config path/to/inventory.json
...                         examples/basic_test.robot
Library           robotframework_vitro.VitroLibrary

Suite Setup       Resolve Suite Devices

*** Keywords ***
Resolve Suite Devices
    ${device_manager}=    Get Device Manager
    ${vitro_config}=      Get Vitro Config
    Set Suite Variable    ${DEVICE_MANAGER}    ${device_manager}
    Set Suite Variable    ${VITRO_CONFIG}      ${vitro_config}

*** Test Cases ***
Vitro Device Manager Is Available
    [Documentation]    Verify the listener deployed devices and the library can reach them.
    Should Not Be Equal    ${DEVICE_MANAGER}    ${NONE}

Vitro Config Is Available
    [Documentation]    Verify the merged config is reachable.
    Should Not Be Equal    ${VITRO_CONFIG}    ${NONE}
