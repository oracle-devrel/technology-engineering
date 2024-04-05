package swierzy.oraclejdbc23newfeatures;
import java.util.concurrent.*;
import java.util.*;

// Subscriber class used in Main.reactiveCallsDemo to demonstrate reactive call to INSERT statement

public class DMLSubscriber<Long> implements Flow.Subscriber<Long> {
    private Flow.Subscription subscription;
    CountDownLatch latch;

    public DMLSubscriber(CountDownLatch latch) {
        super();
        this.latch = latch;
    }

    // onSubscribe is begin called in the background when the subscriber is being subsribed to a publisher
    @Override
    public void onSubscribe(Flow.Subscription subscription) {
        this.subscription = subscription;
        subscription.request(1L);
    }

    // onNext is begin called in the background when publisher propagates a new value
    @Override
    public void onNext(Long item) {
        System.out.println("DMLSubscriber.onNext: Number of rows processed : " + item);
    }

    @Override
    public void onError(Throwable t) {
        t.printStackTrace();
        latch.countDown();
    }

    @Override
    public void onComplete() {
        System.out.println("DMLSubscriber.onComplete: DML statement completed succesfully.");
        latch.countDown();
    }
}
