from celery import chord
from celery_proj.tasks import sample_chord_aggregator, sample_task


def test_chord():
    aggregator = sample_chord_aggregator.s().set(queue="db_write_queue", serializer='pickle')
    chord(sample_task.s(i).set(queue="job_queue",
                               serializer='pickle',
                               result_serializer='pickle')
          for i in range(3))(aggregator)


test_chord()
