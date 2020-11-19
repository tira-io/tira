package de.webis.tira.client.web.response;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Locale;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import scala.actors.threadpool.Arrays;

import com.github.mustachejava.DefaultMustacheFactory;
import com.github.mustachejava.Mustache;
import com.github.mustachejava.MustacheFactory;

import de.webis.tira.client.web.authentication.Authenticator;
import de.webis.tira.client.web.generated.TiraClientWebMessages.User;
import de.webis.tira.client.web.request.Preprocessor;

public class Renderer {
	
	private static final String
		MIME_TYPE_TEXT_HTML_CHARSET_UTF8 = "text/html; charset=UTF-8";
	
	// TODO: Avoid referring explicitly to the supported ui languages.
	public static void 
	render(final ServletContext context, final HttpServletRequest req,
		final HttpServletResponse resp, String template, Object... scopes)
	throws IOException, ServletException {
		File f = new File(context.getRealPath(template));
		// TODO: This is flawed. Try and find a better way to obtain the
		// resource base path.
		final User u = Authenticator.signedInUser(req);
		File resourceBase = f.getParentFile().getParentFile();
		scopes = Arrays.copyOf(scopes, scopes.length + 1);
		scopes[scopes.length - 1] = new Object() {
			@SuppressWarnings("unused")
			String contextPath = 
				Preprocessor.getContextPath(context.getContextPath());
			boolean isSignedIn = Authenticator.isSignedIn(req);
			@SuppressWarnings("unused")
			boolean isReviewer = isSignedIn ? u.getRolesList().contains("reviewer") : false;
			@SuppressWarnings("unused")
			String signedInUserName = isSignedIn ? u.getUserName() : "";
		};
		MustacheFactory mf = new DefaultMustacheFactory(resourceBase);
		Mustache m = mf.compile(template);
		resp.setContentType(MIME_TYPE_TEXT_HTML_CHARSET_UTF8);
		resp.setLocale(Locale.ENGLISH);
		m.execute(new PrintWriter(resp.getOutputStream()), scopes).flush();
	}
}
