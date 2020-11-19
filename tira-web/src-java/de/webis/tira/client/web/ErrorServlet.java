package de.webis.tira.client.web;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.io.Writer;
import java.util.List;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import de.webis.tira.client.web.generated.TiraClientWebMessages.Error;
import de.webis.tira.client.web.request.Preprocessor;
import de.webis.tira.client.web.response.Renderer;
import de.webis.tira.client.web.storage.Directories;
import de.webis.tira.client.web.storage.Identifier;

import com.google.common.collect.Lists;

@WebServlet(ErrorServlet.ROUTE)
@SuppressWarnings("serial")
public class ErrorServlet extends HttpServlet {
	
	public static final String 
		ROUTE = "/error/";

	private static final String 
		TEMPLATE_ERROR = "/templates/tira-error.mustache";

	@Override
	protected void 
	doGet(HttpServletRequest req, HttpServletResponse resp)
	throws ServletException, IOException {
		processRequest(req, resp);
	}
	
	@Override
	protected void
	doPost(HttpServletRequest req, HttpServletResponse resp)
	throws ServletException, IOException {
		processRequest(req, resp);
	}

	private void 
	processRequest(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Error e = processError(req, resp);
		try {
			writeErrorToDisc(e);
		} catch(IOException ioe) {
			// Throwing this error would result in an endless recursion.
			// Therefore, we can only print its trace and hope for the best.
			ioe.printStackTrace();
		}
		Renderer.render(getServletContext(), req, resp, TEMPLATE_ERROR, e);
	}
	
	private Error 
	processError(HttpServletRequest req, HttpServletResponse resp)
	throws IOException {
		Error.Builder eb = Error.newBuilder();
		processUri(req, eb);
		processStatusCode(req, eb);
		processErrorMessage(req, eb);
		processThrowable(req, eb);
		return eb.build();
	}

	private void processUri(HttpServletRequest req, Error.Builder eb) {
		String uri = 
				(String)req.getAttribute(RequestDispatcher.ERROR_REQUEST_URI);
		String contextPath = Preprocessor.getContextPath(req);
		if (uri != null) {
			String scheme = req.getScheme();
		    String serverName = req.getServerName();
		    int serverPort = req.getServerPort();
		    StringBuilder url =  new StringBuilder();
		    url.append(scheme).append("://").append(serverName);
		    if ((serverPort != 80) && (serverPort != 443)) {
		        url.append(":").append(serverPort);
		    }
		    url.append(uri);
			eb.setUrl(url.toString());
		}
		else if(req.getRequestURI().equals(contextPath + ROUTE)) {
			eb.setIsDirect(true);
		}
	}

	private void processStatusCode(HttpServletRequest req, Error.Builder eb) {
		Integer statusCode = 
				(Integer)req.getAttribute(RequestDispatcher.ERROR_STATUS_CODE);
		if (statusCode != null && statusCode != 0) {
			eb.setStatusCode(statusCode);
			if (statusCode.equals(HttpServletResponse.SC_UNAUTHORIZED)) {
				eb.setIs401(true);
			}
			else if (statusCode.equals(HttpServletResponse.SC_NOT_FOUND)) {
				eb.setIs404(true);
			}
		}
	}

	private void processErrorMessage(HttpServletRequest req, Error.Builder eb) {
		String errorMessage = 
				(String)req.getAttribute(RequestDispatcher.ERROR_MESSAGE);
		if (errorMessage != null) {
			eb.setErrorMessage(errorMessage);
		}
	}

	private void processThrowable(HttpServletRequest req, Error.Builder eb) {
		Throwable throwable = 
				(Throwable)req.getAttribute(RequestDispatcher.ERROR_EXCEPTION);
		if (throwable != null) {
			throwable = throwable.getCause();
			if (throwable != null) {
				Writer writer = new StringWriter();
				PrintWriter printWriter = new PrintWriter(writer);
				throwable.printStackTrace(printWriter);
				String stackTrace = writer.toString();
				eb.setStackTrace(stackTrace);
				List<String> causes = Lists.newArrayList();
				causes.add(throwable.getMessage());
				while ((throwable = throwable.getCause()) != null) {
					causes.add(throwable.getMessage());
				}
				eb.addAllCauses(causes);
				eb.setHasCauses(true);
			}
		}
	}
	
	private void writeErrorToDisc(Error e) throws IOException {
		String errorId = Identifier.nextId();
		File f = new File(Directories.ERRORS, errorId + ".bin");
		try (OutputStream out = new FileOutputStream(f)) {
			e.writeTo(out);
		}
	}
}
