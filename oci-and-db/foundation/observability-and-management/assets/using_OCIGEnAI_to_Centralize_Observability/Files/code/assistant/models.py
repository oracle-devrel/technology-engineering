"""Administrator-owned model catalog; browser requests contain aliases, never endpoints."""
import os
import re
from pathlib import Path


class ModelCatalog:
    def __init__(self, settings):
        self.settings = settings
        path = settings.config_dir/'models.json'
        if path.exists():
            config = settings.load('models.json')
        else:
            config = {'default':'default','models':[{'id':'default','label':'Configured OCI model',
                'model_id':settings.model_id,'region':settings.region}]}
        self.default = config['default']
        self.models = {}
        for item in config['models']:
            key, label = item['id'], item['label']
            if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',key) or key in self.models:
                raise ValueError('Model aliases must be unique lowercase names')
            if not isinstance(label,str) or not label.strip() or len(label)>100:
                raise ValueError('Each model needs a short display label')
            region = item.get('region',settings.region)
            if not re.fullmatch(r'[a-z]{2}-[a-z0-9]+-\d+',region):
                raise ValueError('Invalid OCI model region')
            if item.get('model_id_env'):
                variable = item['model_id_env']
                if not re.fullmatch(r'GENAI_[A-Z0-9_]+',variable):
                    raise ValueError('Model ID variables must use the GENAI_ prefix')
                model_id = settings.model_id if variable=='GENAI_MODEL_ID' else os.getenv(variable,'')
            else:
                model_id = item.get('model_id','')
            configured = isinstance(model_id,str) and model_id.startswith('ocid1.generativeaimodel.') and 'REPLACE' not in model_id
            enabled = item.get('enabled',True) is True and (configured or settings.mode=='demo')
            self.models[key] = {'id':key,'label':label.strip(),'region':region,'model_id':model_id,'enabled':enabled}
        if self.default not in self.models:
            raise ValueError('The default model must exist in the model catalog')

    def public(self):
        return [{k:m[k] for k in ('id','label','region','enabled')} for m in self.models.values()]

    def resolve(self, key=None):
        model = self.models.get(key or self.default)
        if model is None or not model['enabled']:
            raise ValueError('That model is unavailable. Choose an enabled model or ask the administrator to configure it.')
        return dict(model)
