package de.webis.tira.client.web.authentication;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;

import de.webis.tira.client.web.generated.TiraClientWebMessages.User;
import de.webis.tira.client.web.storage.UsersStore;

public class Authenticator {

	public static final boolean 
	isSignedIn(HttpServletRequest req)
	throws ServletException {
		return Authenticator.signedInUser(req) != null;
	}

	/**
	 * Returns a Tira user object if an existing username was with the Disraptor user header.
	 * 
	 * @param req The incoming request.
	 * @return a Tira user object.
	 * @throws ServletException
	 */
	public static final User
	signedInUser(HttpServletRequest req)
	throws ServletException {
		String userName = req.getHeader("X-Disraptor-User");

		if (userName != null) {
			return UsersStore.getUser(userName);
		}

		return null;
	}
}
