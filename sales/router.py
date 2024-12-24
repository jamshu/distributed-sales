class ShardedDatabaseRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'sales':
            retail_point_id = hints.get('retail_point_id')
            return f'shard_{retail_point_id}' if retail_point_id else 'default'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'sales':
            retail_point_id = hints.get('retail_point_id')
            return f'shard_{retail_point_id}' if retail_point_id else 'default'
        return 'default'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True
    
    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations only if both objects use the same database
        return obj1._state.db == obj2._state.db


