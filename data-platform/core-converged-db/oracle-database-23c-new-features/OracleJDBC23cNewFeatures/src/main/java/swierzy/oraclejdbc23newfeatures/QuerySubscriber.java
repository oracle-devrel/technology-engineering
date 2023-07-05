package swierzy.oraclejdbc23newfeatures;
import oracle.jdbc.*;
import java.sql.*;
import java.util.LinkedList;
import java.util.List;
import java.util.concurrent.*;

// Subscriber class used in Main.reactiveCallsDemoo to demonstrate reactive call to SELECT statement
public class QuerySubscriber<OracleResultSet> implements Flow.Subscriber<OracleResultSet> {
    private Flow.Subscription subscription;
    private CountDownLatch latch;
    public QuerySubscriber(CountDownLatch latch) {
        super();
        this.latch = latch;
    }

    // onSubscribe is begin called in the background when the subscriber is being subsribed to a publisher
    public void onSubscribe(Flow.Subscription subscription) {
        this.subscription = subscription;
        subscription.request(Long.MAX_VALUE);
    }

    // onNext is begin called in the background when publisher propagates a new value
    @Override
    public void onNext(OracleResultSet item) {
        try {
            ((ResultSet) item).next();
            System.out.println("QuerySubscriber.onNext: Number of rows in TEST table : "+((ResultSet) item).getNString(1));
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onError(Throwable t) {
        t.printStackTrace();
        latch.countDown();
    }

    @Override
    public void onComplete() {
        System.out.println("QuerySubscriber.onComplete: SELECT statement completed succesfully.");
        latch.countDown();
    }
}