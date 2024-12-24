# sales/validators.py
import jsonschema

def validate_sale_data(data):
    sale_schema = {
        "type": "object",
        "properties": {
            "retail_point_id": {"type": "number"},
            "sale_counter_id": {"type": "number"},
            "total_including_miscellaneous": {"type": "number"},
            "payment_journal_id": {"type": "number"},
            "sale_num": {"type": "string"},
            "sale_line_ids": {
                "type": "array",
                "sale_line_ids": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "number"},
                        "name": {"type": "string"},
                        "product_uom_qty": {"type": "number"},
                        "price_unit": {"type": "number"},
                        "product_uom": {"type": "number"}
                    },
                    "required": ["product_id", "name", "product_uom_qty",
                                 "price_unit", "product_uom"]
                }
            }
        },
        "required": ["retail_point_id", "sale_counter_id",
                     "total_including_miscellaneous", "payment_journal_id",]
    }

    try:
        jsonschema.validate(instance=data, schema=sale_schema)
        return data
    except jsonschema.ValidationError as e:
        raise ValueError(f"Invalid sale data: {e}")
