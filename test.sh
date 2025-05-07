#!/bin/bash

MODULE_NAME=module1
MODULE_NEXT_VERSION=0.0.3
JSON_STRING=$( jq -n -c \
    --arg bn "$MODULE_NAME" \
    --arg on "$MODULE_NEXT_VERSION" \
    '{module_name: $bn, module_next_version: $on}' )
echo $JSON_STRING
echo jq -c $JSON_STRING
