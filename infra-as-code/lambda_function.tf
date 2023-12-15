data "archive_file" "zip_the_python_code" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_code/"
  output_path = "${path.module}/lambda_code/lambda_code.zip"
}

resource "aws_lambda_function" "lambda_function" {
  filename         = data.archive_file.zip_the_python_code.output_path
  function_name    = "${var.step_function_name}_${var.environment}-lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_code.lambda_handler"
  source_code_hash = data.archive_file.zip_the_python_code.output_base64sha256
  runtime          = "python3.8"
  timeout          = 600
}