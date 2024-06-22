from django.db import models
from apps.agent_manager.models.agent import Agent
from apps.risk_manager.models.commission_realized import CommissionRealized

class AgentRevenue(models.Model):
    agent = models.ForeignKey(Agent, related_name='revenues', on_delete=models.SET_NULL, null=True, blank=True)
    commission_realized = models.ForeignKey(CommissionRealized, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.FloatField()

    def __str__(self):
        return f"{self.agent}, {self.amount}"

    class Meta:
        # ordering = ['-status_changed_at']
        verbose_name_plural = "       Agent Revenues"
        db_table = 'agent_revenues'