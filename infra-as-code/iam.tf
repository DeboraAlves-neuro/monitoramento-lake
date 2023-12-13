resource "aws_iam_role" "step_function_role" {
  name               = "${var.step_function_name}_${var.environment}-role"
  assume_role_policy = <<-EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "sts:AssumeRole",
        "Principal": {
          "Service": "states.amazonaws.com"
        },
        "Effect": "Allow",
        "Sid": "StepFunctionAssumeRole"
      }
    ]
  }
  EOF
}

resource "aws_iam_role_policy" "step_function_policy" {
  name   = "${var.step_function_name}_${var.environment}-policy"
  role   = aws_iam_role.step_function_role.id
  policy = <<-EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution"
        ],
        "Resource": "*"
      },
      {
        "Sid": "S3ListAndRead",
        "Effect": "Allow",
        "Action": [
          "s3:Get*",
          "s3:PutBucketTagging",
          "s3:ListBucketVersions",
          "s3:ListBucket"
        ],
        "Resource": [
          "arn:aws:s3:::dev-neurolake-consumption",
          "arn:aws:s3:::dev-neurolake-bridge",
          "arn:aws:s3:::dev-neurolake-ingestion",
          "arn:aws:s3:::neurolake-data-nl-consumption",
          "arn:aws:s3:::neurolake-data-nl-bridge",
          "arn:aws:s3:::dev-neurolake-governanca-dados",
          "arn:aws:s3:::dev-neurolake-domain",
          "arn:aws:s3:::neurolake-data-monitoring",
          "arn:aws:s3:::neurolake-alfred_logs"
        ]
      },
      {
        "Sid": "S3ListReadPutAndDelete",
        "Effect": "Allow",
        "Action": [
          "s3:Get*",
          "s3:Put*",
          "s3:List*",
          "s3:Abort*",
          "s3:Delete*", 
          "s3:Create*",
          "s3:Restore*"
        ],
        "Resource": [
          "arn:aws:s3:::dev-neurolake-sandbox",
          "arn:aws:s3:::dev-neurolake-sandbox/*",
          "arn:aws:s3:::aws-athena-query-results-584584486681-us-east-1",
          "arn:aws:s3:::aws-athena-query-results-584584486681-us-east-1/*",
          "arn:aws:s3:::aws-athena-query-results-*",
          "arn:aws:s3:::neurolake-data-monitoring",
          "arn:aws:s3:::neurolake-data-monitoring/*"
        ]
      },
      {
        "Sid": "LakeFormationDataAccess",
        "Effect": "Allow",
        "Action": "lakeformation:GetDataAccess",
        "Resource": "*"
      },
      {
        "Sid": "GlueFullReadAccess",
        "Effect": "Allow",
        "Action": [
          "glue:SearchTables",
          "glue:GetDatabase",
          "glue:DeleteDatabase",
          "glue:GetUserDefinedFunction",
          "glue:CreateTable",
          "glue:GetTables",
          "lakeformation:GetDataAccess",
          "glue:GetPartitions",
          "glue:DeleteTable",
          "glue:GetDatabases",
          "glue:GetUserDefinedFunctions",
          "glue:GetTable",
          "glue:BatchCreatePartition",
          "glue:UpdateTable",
          "glue:GetPartition",
          "glue:DeletePartition"
        ],
        "Resource": "*"
      },
      {
        "Action": "lambda:InvokeFunction",
        "Effect": "Allow",
        "Resource": "${aws_lambda_function.lambda_function.arn}"
      },
      {
        "Sid": "CloudWatchEventsFullAccess",
        "Effect": "Allow",
        "Action": "events:*",
        "Resource": "*"
      },
      {
        "Sid": "IAMPassRoleForCloudWatchEvents",
        "Effect": "Allow",
        "Action": "iam:PassRole",
        "Resource": "arn:aws:iam::*:role/AWS_Events_Invoke_Targets"
      }
    ]
  }
  EOF
}

resource "aws_iam_role" "lambda_role" {
  name               = "${var.step_function_name}_${var.environment}-lambda-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": "LambdaAssumeRole"
    }
  ]
}
  EOF
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.step_function_name}_${var.environment}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = <<-EOF
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "GlueFullReadAccess",
          "Effect": "Allow",
          "Action": [
            "lakeformation:GetDataAccess",
            "glue:Get*",
            "glue:Batch*",
            "glue:Search*",
            "glue:DeleteTable",
            "glue:CreateTable"
          ],
          "Resource": "*"
        },
        {
          "Effect": "Allow",
          "Action": [
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents",
            "logs:DescribeLogStreams"
          ],
          "Resource": "arn:aws:logs:*:*:*"
        },
        {
          "Effect": "Allow",
          "Action": "secretsmanager:GetSecretValue",
          "Resource": "arn:aws:secretsmanager:us-east-1:584584486681:secret:neurolake/governance/aws_prd/access_keys-KjRybO"
        },
        {
          "Sid": "S3ListAndRead",
          "Effect": "Allow",
          "Action": [
            "s3:Get*",
            "s3:PutBucketTagging",
            "s3:ListBucketVersions",
            "s3:List*"
          ],
          "Resource": [
            "arn:aws:s3:::dev-neurolake-consumption",
            "arn:aws:s3:::dev-neurolake-consumption/*",
            "arn:aws:s3:::dev-neurolake-bridge",
            "arn:aws:s3:::dev-neurolake-bridge/*",
            "arn:aws:s3:::dev-neurolake-ingestion",
            "arn:aws:s3:::dev-neurolake-ingestion/*",
            "arn:aws:s3:::neurolake-data-nl-consumption",
            "arn:aws:s3:::neurolake-data-nl-consumption/*",
            "arn:aws:s3:::neurolake-data-nl-bridge",
            "arn:aws:s3:::neurolake-data-nl-bridge/*",
            "arn:aws:s3:::dev-neurolake-governanca-dados",
            "arn:aws:s3:::dev-neurolake-governanca-dados/*",
            "arn:aws:s3:::neurolake-alfred_logs"
          ]
        },
        {
          "Effect": "Allow",
          "Action": [
            "s3:List*",
            "s3:Delete*",
            "s3:Get*",
            "s3:Put*"
          ],
          "Resource": [
            "arn:aws:s3:::dev-neurolake-consumption/*",
            "arn:aws:s3:::dev-neurolake-bridge/*",
            "arn:aws:s3:::dev-neurolake-sandbox/*",
            "arn:aws:s3:::dev-neurolake-ingestion/*",
            "arn:aws:s3:::dev-neurolake-consumption",
            "arn:aws:s3:::dev-neurolake-bridge",
            "arn:aws:s3:::dev-neurolake-sandbox",
            "arn:aws:s3:::dev-neurolake-ingestion",
            "arn:aws:s3:::neurolake-data-nl-bridge",
            "arn:aws:s3:::neurolake-data-nl-bridge/*",
            "arn:aws:s3:::neurolake-data-nl-consumption",
            "arn:aws:s3:::neurolake-data-nl-consumption/*",
            "arn:aws:s3:::dev-neurolake-governanca-dados",
            "arn:aws:s3:::dev-neurolake-governanca-dados/*",
            "arn:aws:s3:::neurolake-data-monitoring",
            "arn:aws:s3:::neurolake-data-monitoring/*",
            "arn:aws:s3:::neurolake-alfred_logs"
          ]
        }
      ]
    }
    EOF
}