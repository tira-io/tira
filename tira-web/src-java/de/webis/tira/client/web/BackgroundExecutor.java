package de.webis.tira.client.web;

import java.io.InputStream;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import javax.servlet.ServletContext;
import javax.servlet.ServletContextEvent;
import javax.servlet.ServletContextListener;
import javax.servlet.annotation.WebListener;

import org.apache.commons.io.IOUtils;

@WebListener
public class BackgroundExecutor implements ServletContextListener {

	public static final Object 
		LOCK = new Object();
	
	public static final String
		ATTRIBUTE_NAME = BackgroundExecutor.class.getSimpleName();
	
	private ExecutorService executor;
	
	@Override
	public void contextInitialized(ServletContextEvent sce) {
		executor = Executors.newCachedThreadPool();
		sce.getServletContext().setAttribute(ATTRIBUTE_NAME, executor);
	}

	@Override
	public void contextDestroyed(ServletContextEvent sce) {
		executor.shutdown();
		try {
			executor.awaitTermination(10, TimeUnit.SECONDS);
		} catch (InterruptedException e) {
			e.printStackTrace(System.err);
			executor.shutdownNow();
		}
	}
	
	public static Future<String>
	dispatchStreamReader(ServletContext sc, final InputStream is) {
		final ExecutorService es = 
				(ExecutorService)sc.getAttribute(ATTRIBUTE_NAME);
		
		return es.submit(new Callable<String>() {

			@Override
			public String call() throws Exception {
				return IOUtils.toString(is);
			}
		});
	}
}
