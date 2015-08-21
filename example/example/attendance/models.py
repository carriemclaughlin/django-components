
from django.db import models

class AttendanceRecord(models.Model):
    name = models.CharField(max_length=75)
    arrival_time = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s attended at %s (id-%s)' % (self.name,
                                               self.arrival_time,
                                               self.id)

