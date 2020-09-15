from aws_cdk import aws_apigateway as _apigw
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as _logs
from aws_cdk import core

import json
import os


class GlobalArgs:
    """
    Helper to define global statics
    """

    OWNER = "MystiqueAutomation"
    ENVIRONMENT = "production"
    REPO_NAME = "api-request-validation"
    SOURCE_INFO = f"https://github.com/miztiik/{REPO_NAME}"
    VERSION = "2020_09_10"
    MIZTIIK_SUPPORT_EMAIL = ["mystique@example.com", ]


class ApiRequestValidationStack(core.Stack):

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        stack_log_level: str,
        back_end_api_name: str,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # Read Lambda Code):
        try:
            with open("api_request_validation/stacks/back_end/lambda_src/serverless_greeter.py", mode="r") as f:
                greeter_fn_code = f.read()
        except OSError as e:
            print("Unable to read Lambda Function Code")
            raise e

        greeter_fn = _lambda.Function(
            self,
            "secureGreeterFn",
            function_name=f"greeter_fn_{id}",
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler="index.lambda_handler",
            code=_lambda.InlineCode(greeter_fn_code),
            current_version_options={
                "removal_policy": core.RemovalPolicy.DESTROY,  # Remove old versions
                "retry_attempts": 1,
                "description": "Mystique Factory Build Version"
            },
            timeout=core.Duration.seconds(5),
            reserved_concurrent_executions=10,
            environment={
                "LOG_LEVEL": f"{stack_log_level}",
                "Environment": "Production",
                "ANDON_CORD_PULLED": "False",
                "RANDOM_SLEEP_ENABLED": "False",
                "RANDOM_SLEEP_SECS": "2",
            },
            description="A simple greeter function, which responds with a timestamp"
        )

        greeter_fn_version_alias = greeter_fn.current_version.add_alias(
            "MystiqueAutomation")
        greeter_fn_prod_alias = greeter_fn.current_version.add_alias("prod")

        # Create Custom Loggroup
        greeter_fn_lg = _logs.LogGroup(
            self,
            "squareFnLoggroup",
            log_group_name=f"/aws/lambda/{greeter_fn.function_name}",
            retention=_logs.RetentionDays.ONE_WEEK,
            removal_policy=core.RemovalPolicy.DESTROY
        )

# %%
        #######################################
        ##    CONFIG FOR API STAGE : PROD    ##
        #######################################
        wa_api_logs = _logs.LogGroup(
            self,
            "waApiLogs",
            log_group_name=f"/aws/apigateway/{back_end_api_name}/access_logs",
            removal_policy=core.RemovalPolicy.DESTROY,
            retention=_logs.RetentionDays.ONE_DAY
        )

        # Add API GW front end for the Lambda
        prod_api_stage_options = _apigw.StageOptions(
            stage_name="miztiik",
            throttling_rate_limit=10,
            throttling_burst_limit=100,
            # Log full requests/responses data
            data_trace_enabled=True,
            # Enable Detailed CloudWatch Metrics
            metrics_enabled=True,
            logging_level=_apigw.MethodLoggingLevel.INFO,
            access_log_destination=_apigw.LogGroupLogDestination(wa_api_logs),
            variables={
                "lambdaAlias": "prod",
                "appOwner": "Mystique"
            }
        )

        # Create API Gateway
        wa_api = _apigw.RestApi(
            self,
            "backEnd01Api",
            rest_api_name=f"{back_end_api_name}",
            deploy_options=prod_api_stage_options,
            minimum_compression_size=0,
            endpoint_types=[
                _apigw.EndpointType.EDGE
            ],
            description=f"{GlobalArgs.OWNER}: API Best Practice Demonstration. Validate HTTP Requests at API Gateway"
        )

        wa_api_res = wa_api.root.add_resource("well-architected-api")
        stationary_by_category = wa_api_res.add_resource("get-stationary")

        # Because this is NOT a proxy integration, we need to define our response model
        response_model = wa_api.add_model(
            "ResponseModel",
            content_type="application/json",
            model_name="MiztiikResponseModel",
            schema=_apigw.JsonSchema(
                schema=_apigw.JsonSchemaVersion.DRAFT4,
                title="updateResponse",
                type=_apigw.JsonSchemaType.OBJECT,
                properties={
                    "message": _apigw.JsonSchema(type=_apigw.JsonSchemaType.STRING)
                }
            )
        )

        # "pencil": [{"id": 1, "type": "microtip", "status": "unavailable", "price": 19}]
        req_model_stationary = wa_api.add_model(
            "RequestModel",
            content_type="application/json",
            model_name="RequestModelForStationary",
            schema=_apigw.JsonSchema(
                schema=_apigw.JsonSchemaVersion.DRAFT4,
                title="RequestValidation",
                type=_apigw.JsonSchemaType.OBJECT,
                properties={
                    "category": {
                        "type": _apigw.JsonSchemaType.STRING,
                        "enum": ["pens", "pencil", "eraser"]
                    }
                },
                required=["category"]
            )
        )

        stationary_by_category_req_validator = wa_api.add_request_validator(
            "apiReqValidator",
            validate_request_parameters=True,
            validate_request_body=True
        )

        req_template = """$input.json('$')"""

        # resp_template = """$input.path('$.body.message')"""
        resp_template = """$input.path('$.body')"""

        stationary_by_category_method_get = stationary_by_category.add_method(
            http_method="POST",
            request_parameters={
                "method.request.header.InvocationType": False,
                "method.request.path.category": False
            },
            request_models={
                "application/json": req_model_stationary
            },
            request_validator=stationary_by_category_req_validator,
            integration=_apigw.LambdaIntegration(
                handler=greeter_fn,
                proxy=False,
                request_parameters={
                    "integration.request.path.category": "method.request.path.category"
                },
                cache_key_parameters=[
                    "method.request.path.category"
                ],
                request_templates={
                    "application/json": req_template
                },
                passthrough_behavior=_apigw.PassthroughBehavior.NEVER,
                integration_responses=[
                    _apigw.IntegrationResponse(
                        status_code="200",
                        # selection_pattern="2\d{2}",  # Use for mapping Lambda Errors
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Headers": "'cache-control,Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                            "method.response.header.Content-Type": "'application/json'",
                        },
                        response_templates={
                            "application/json": f"{resp_template}"
                        }
                    )
                ]
            ),
            method_responses=[
                _apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Content-Type": True,
                        "method.response.header.Access-Control-Allow-Headers": True,
                    },
                    response_models={
                        "application/json": response_model
                    }
                ),
                _apigw.MethodResponse(
                    status_code="400",
                    response_parameters={
                        "method.response.header.Content-Length": True,
                    },
                    response_models={
                        "application/json": _apigw.EmptyModel()
                    }
                )
            ]
        )

        # Outputs
        output_0 = core.CfnOutput(
            self,
            "AutomationFrom",
            value=f"{GlobalArgs.SOURCE_INFO}",
            description="To know more about this automation stack, check out our github page."
        )

        output_1 = core.CfnOutput(
            self,
            "WellArchitectedApiUrl",
            value=f"{stationary_by_category.url}",
            description="Use an utility like curl from the same VPC as the API to invoke it."
        )
