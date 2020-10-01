#!/usr/bin/env python3

from api_request_validation.stacks.back_end.api_request_validation_stack import ApiRequestValidationStack
from aws_cdk import core


app = core.App()


api_request_validation = ApiRequestValidationStack(
    app,
    "api-request-validation",
    stack_log_level="INFO",
    back_end_api_name="api-request-validation",
    description="Miztiik Automation: API Best Practice Demonstration. Validate HTTP Requests at API Gateway"
)


# Stack Level Tagging
core.Tag.add(app, key="Owner",
             value=app.node.try_get_context("owner"))
core.Tag.add(app, key="OwnerProfile",
             value=app.node.try_get_context("github_profile"))
core.Tag.add(app, key="Project",
             value=app.node.try_get_context("service_name"))
core.Tag.add(app, key="GithubRepo",
             value=app.node.try_get_context("github_repo_url"))
core.Tag.add(app, key="Udemy",
             value=app.node.try_get_context("udemy_profile"))
core.Tag.add(app, key="SkillShare",
             value=app.node.try_get_context("skill_profile"))
core.Tag.add(app, key="AboutMe",
             value=app.node.try_get_context("about_me"))
core.Tag.add(app, key="BuyMeACoffee",
             value=app.node.try_get_context("ko_fi"))

app.synth()
