#!/usr/bin/env python3

from aws_cdk import core

from api_request_validation.api_request_validation_stack import ApiRequestValidationStack


app = core.App()
ApiRequestValidationStack(app, "api-request-validation")

app.synth()
