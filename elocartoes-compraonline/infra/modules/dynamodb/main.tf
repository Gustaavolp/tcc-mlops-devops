# -----------------------------------------------------------------------------
# DynamoDB Table
# -----------------------------------------------------------------------------

resource "aws_dynamodb_table" "this" {
  name         = "${var.project_name}-${var.table_name_suffix}-${var.environment}"
  billing_mode = var.billing_mode
  hash_key     = var.hash_key
  range_key    = var.range_key

  # Partition Key (hash key)
  attribute {
    name = var.hash_key
    type = var.hash_key_type
  }

  # Sort Key (range key)
  attribute {
    name = var.range_key
    type = var.range_key_type
  }

  # Point-in-Time Recovery
  point_in_time_recovery {
    enabled = var.point_in_time_recovery_enabled
  }

  # Deletion Protection
  deletion_protection_enabled = var.deletion_protection_enabled

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.table_name_suffix}-${var.environment}"
      Environment = var.environment
    }
  )
}
