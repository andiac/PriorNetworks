import torch
from torch.nn import functional as F


class EnDLoss:
    def __init__(self):
        pass

    def __call__(self, *args):
        return self.forward(*args)

    def forward(self, logits, teacher_logits, temp):
        # TODO: Should I multiply by temp**2 ?
        teacher_probs = F.softmax(teacher_logits / temp, dim=2)
        teacher_probs_mean = torch.mean(teacher_probs, dim=1)

        cost = - teacher_probs_mean * F.log_softmax(logits / temp, dim=1) * (temp ** 2)

        assert torch.all(torch.isfinite(cost)).item()

        return torch.mean(cost)


class DirichletEnDDLoss(object):
    """Standard Negative Log-likelihood of the ensemble predictions"""

    def __init__(self, smoothing=1e-8, teacher_prob_smoothing=1e-3):
        self.smooth_val = smoothing
        self.tp_scaling = 1 - teacher_prob_smoothing

    def __call__(self, *args):
        return self.forward(*args)

    def forward(self, logits, teacher_logits, temp=1.0):
        alphas = torch.exp(logits / temp)
        precision = torch.sum(alphas, dim=1)

        teacher_probs = F.softmax(teacher_logits / temp, dim=2)
        # Smooth for num. stability:
        probs_mean = 1 / (teacher_probs.size()[2])
        # Subtract mean, scale down, add mean back)
        teacher_probs = self.tp_scaling * (teacher_probs - probs_mean) + probs_mean
        assert torch.all(teacher_probs != 0).item()

        log_teacher_probs_geo_mean = torch.mean(torch.log(teacher_probs + self.smooth_val), dim=1)
        assert torch.all(torch.isfinite(log_teacher_probs_geo_mean)).item()

        # Define the cost in two parts (dependent on targets and independent of targets)
        target_independent_term = torch.sum(torch.lgamma(alphas + self.smooth_val), dim=1) \
                                  - torch.lgamma(precision + self.smooth_val)
        assert torch.all(torch.isfinite(target_independent_term)).item()

        target_dependent_term = - torch.sum((alphas - 1.) * log_teacher_probs_geo_mean, dim=1)
        assert torch.all(torch.isfinite(target_dependent_term)).item()

        cost = target_dependent_term + target_independent_term
        assert torch.all(torch.isfinite(cost)).item()

        return torch.mean(cost) * (temp ** 2)

class DirichletEnDDEnTempLoss(object):
    """Standard Negative Log-likelihood of the ensemble predictions"""

    def __init__(self, smoothing=1e-8, teacher_prob_smoothing=1e-3):
        self.smooth_val = smoothing
        self.tp_scaling = 1 - teacher_prob_smoothing

    def __call__(self, *args):
        return self.forward(*args)

    def forward(self, logits, teacher_logits, temp=1.0):
        alphas = torch.exp(logits)
        precision = torch.sum(alphas, dim=1)

        teacher_probs = F.softmax(teacher_logits / temp, dim=2)
        # Smooth for num. stability:
        probs_mean = 1 / (teacher_probs.size()[2])
        # Subtract mean, scale down, add mean back)
        teacher_probs = self.tp_scaling * (teacher_probs - probs_mean) + probs_mean
        assert torch.all(teacher_probs != 0).item()

        log_teacher_probs_geo_mean = torch.mean(torch.log(teacher_probs + self.smooth_val), dim=1)
        assert torch.all(torch.isfinite(log_teacher_probs_geo_mean)).item()

        # Define the cost in two parts (dependent on targets and independent of targets)
        target_independent_term = torch.sum(torch.lgamma(alphas + self.smooth_val), dim=1) \
                                  - torch.lgamma(precision + self.smooth_val)
        assert torch.all(torch.isfinite(target_independent_term)).item()

        target_dependent_term = - torch.sum((alphas - 1.) * log_teacher_probs_geo_mean, dim=1)
        assert torch.all(torch.isfinite(target_dependent_term)).item()

        cost = target_dependent_term + target_independent_term
        assert torch.all(torch.isfinite(cost)).item()

        return torch.mean(cost)

class DirichletEnDDDirTempLoss(object):
    """Standard Negative Log-likelihood of the ensemble predictions"""

    def __init__(self, smoothing=1e-8, teacher_prob_smoothing=1e-3):
        self.smooth_val = smoothing
        self.tp_scaling = 1 - teacher_prob_smoothing

    def __call__(self, *args):
        return self.forward(*args)

    def forward(self, logits, teacher_logits, temp=1.0):
        alphas = torch.exp(logits / temp)
        precision = torch.sum(alphas, dim=1)

        teacher_probs = F.softmax(teacher_logits, dim=2)
        # Smooth for num. stability:
        probs_mean = 1 / (teacher_probs.size()[2])
        # Subtract mean, scale down, add mean back)
        teacher_probs = self.tp_scaling * (teacher_probs - probs_mean) + probs_mean
        assert torch.all(teacher_probs != 0).item()

        log_teacher_probs_geo_mean = torch.mean(torch.log(teacher_probs + self.smooth_val), dim=1)
        assert torch.all(torch.isfinite(log_teacher_probs_geo_mean)).item()

        # Define the cost in two parts (dependent on targets and independent of targets)
        target_independent_term = torch.sum(torch.lgamma(alphas + self.smooth_val), dim=1) \
                                  - torch.lgamma(precision + self.smooth_val)
        assert torch.all(torch.isfinite(target_independent_term)).item()

        target_dependent_term = - torch.sum((alphas - 1.) * log_teacher_probs_geo_mean, dim=1)
        assert torch.all(torch.isfinite(target_dependent_term)).item()

        cost = target_dependent_term + target_independent_term
        assert torch.all(torch.isfinite(cost)).item()

        return torch.mean(cost) * (temp ** 2)

class DirichletEnDDRevLoss(object):
    """Standard Negative Log-likelihood of the ensemble predictions"""

    def __init__(self, smoothing=1e-8, teacher_prob_smoothing=1e-3):
        self.smooth_val = smoothing
        self.tp_scaling = 1 - teacher_prob_smoothing

    def __call__(self, *args):
        return self.forward(*args)

    def forward(self, logits, teacher_logits, temp=1.0):
        alphas = torch.exp(logits * temp)
        precision = torch.sum(alphas, dim=1)

        teacher_probs = F.softmax(teacher_logits / temp, dim=2)
        # Smooth for num. stability:
        probs_mean = 1 / (teacher_probs.size()[2])
        # Subtract mean, scale down, add mean back)
        teacher_probs = self.tp_scaling * (teacher_probs - probs_mean) + probs_mean
        assert torch.all(teacher_probs != 0).item()

        log_teacher_probs_geo_mean = torch.mean(torch.log(teacher_probs + self.smooth_val), dim=1)
        assert torch.all(torch.isfinite(log_teacher_probs_geo_mean)).item()

        # Define the cost in two parts (dependent on targets and independent of targets)
        target_independent_term = torch.sum(torch.lgamma(alphas + self.smooth_val), dim=1) \
                                  - torch.lgamma(precision + self.smooth_val)
        assert torch.all(torch.isfinite(target_independent_term)).item()

        target_dependent_term = - torch.sum((alphas - 1.) * log_teacher_probs_geo_mean, dim=1)
        assert torch.all(torch.isfinite(target_dependent_term)).item()

        cost = target_dependent_term + target_independent_term
        assert torch.all(torch.isfinite(cost)).item()

        return torch.mean(cost) / (temp ** 2)